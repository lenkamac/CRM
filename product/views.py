import json
from multiprocessing import context
from datetime import date as date_type
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, ExpressionWrapper, DecimalField, F
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View

from client.forms import PurchaseForm
from client.models import Purchase, Client
from core.currency_service import CurrencyConverter
from product.models import Product
from django.views.generic import ListView, DetailView


# Create your views here.
class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'product/products-list.html'
    context_object_name = 'products'

    def get_queryset(self):
        qs = Product.objects.filter(
            Q(created_by=self.request.user) | Q(created_by__isnull=True)
        )
        sort = self.request.GET.get('sort')
        if sort == 'name_asc':
            return qs.order_by('name')
        elif sort == 'name_desc':
            return qs.order_by('-name')
        return qs.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort'] = self.request.GET.get('sort', '')
        return context


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'product/product-detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all purchases for this product
        context['purchases'] = self.object.purchases.all().select_related('client', 'created_by').annotate(
            total_price=ExpressionWrapper(
                F('quantity') * F('purchase_price'),
                output_field=DecimalField()
            )
        )

        context['sort'] = self.request.GET.get('sort','')
        sort = context['sort']
        if sort == 'date_asc':
            context['purchases'] = context['purchases'].order_by('created_at')
        elif sort == 'date_desc':
            context['purchases'] = context['purchases'].order_by('-created_at')

        if sort == 'quantity_asc':
            context['purchases'] = context['purchases'].order_by('quantity')
        elif sort == 'quantity_desc':
            context['purchases'] = context['purchases'].order_by('-quantity')

        if sort == 'total_asc':
            context['purchases'] = context['purchases'].order_by('total_price')
        elif sort == 'total_desc':
            context['purchases'] = context['purchases'].order_by('-total_price')

        # pagination
        purchase_list = context['purchases']
        paginator = Paginator(purchase_list, 25)
        page_number = self.request.GET.get('page')
        context['purchases'] = paginator.get_page(page_number)

        return context


@login_required
def add_product(request):
    """Add a new product"""
    if request.method == 'POST':
        name = request.POST.get('name')
        net_price = request.POST.get('net_price')
        sold_quantity = request.POST.get('sold_quantity', 0)
        description = request.POST.get('description', '')

        # Create new product
        Product.objects.create(
            name=name,
            net_price=net_price,
            sold_quantity=sold_quantity,
            description=description,
            created_by=request.user,
        )

        messages.success(request, 'Product added successfully!')
        return redirect('product:product_list')

    return render(request, 'product/add-product.html')


def delete_product(request, product_id):
    """Delete a product"""
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" has been deleted successfully!')
        return redirect('product:product_list')

    return render(request, 'product/delete-product.html', {'product': product})


def edit_product(request, product_id):
    """Edit an existing product"""
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.net_price = request.POST.get('net_price')
        product.sold_quantity = request.POST.get('sold_quantity', 0)
        product.description = request.POST.get('description', '')

        product.save()

        messages.success(request, f'Product "{product.name}" has been updated successfully!')
        return redirect('product:product_list')

    return render(request, 'product/edit-product.html', {'product': product})


@login_required
def product_autocomplete(request):
    query = request.GET.get('q', '').strip()
    user_filter = Q(created_by=request.user) | Q(created_by__isnull=True)
    if query:
        products = Product.objects.filter(user_filter, name__istartswith=query).values('id', 'name')
    else:
        products = Product.objects.filter(user_filter).values('id', 'name')[:50]
    results = [{'id': p['id'], 'label': p['name']} for p in products]
    return JsonResponse(results, safe=False)


class AddPurchaseGenericView(LoginRequiredMixin, View):
    """Add purchase from the sales list — client is selected via autocomplete."""

    def get(self, request):
        purchaseform = PurchaseForm()
        products = Product.objects.all().values('id', 'name', 'net_price')
        products_dict = {str(p['id']): str(p['net_price']) for p in products}
        try:
            exchange_rate = float(CurrencyConverter.get_exchange_rate('EUR', 'USD'))
        except Exception:
            exchange_rate = 1.10
        return render(request, 'product/add_purchase.html', {
            'purchaseform': purchaseform,
            'products_json': json.dumps(products_dict),
            'exchange_rate': json.dumps(exchange_rate),
        })

    def post(self, request):
        client_id = request.POST.get('client_id', '').strip()
        client = get_object_or_404(Client, pk=client_id, created_by=request.user)
        cart_data = request.POST.get('cart_data', '')
        general_notes = request.POST.get('notes', '')

        if cart_data:
            try:
                cart_items = json.loads(cart_data)
                if not cart_items:
                    messages.error(request, 'Please add at least one product to the cart')
                    return redirect('product:add_purchase_generic')

                purchase_count = 0
                total_amount_eur = 0
                total_amount_usd = 0

                for item in cart_items:
                    product = Product.objects.get(id=item['productId'])
                    purchase = Purchase(
                        client=client,
                        product=product,
                        quantity=item['quantity'],
                        purchase_price=item['price'],
                        currency=item['currency'],
                        notes=f"{item.get('notes', '')}\n{general_notes}".strip(),
                        created_at=datetime.strptime(item['createdAt'], '%d.%m.%Y'),
                        created_by=request.user,
                    )
                    purchase.save()
                    purchase_count += 1

                    if item['currency'] == 'EUR':
                        total_amount_eur += item['quantity'] * item['price']
                    else:
                        exchange_rate = float(CurrencyConverter.get_exchange_rate('EUR', 'USD'))
                        total_amount_eur += (item['quantity'] * item['price']) / exchange_rate
                        total_amount_usd += item['quantity'] * item['price']

                if total_amount_eur > 0 and total_amount_usd == 0:
                    exchange_rate = float(CurrencyConverter.get_exchange_rate('EUR', 'USD'))
                    total_amount_usd = total_amount_eur * exchange_rate
                elif total_amount_usd > 0 and total_amount_eur == 0:
                    exchange_rate = float(CurrencyConverter.get_exchange_rate('EUR', 'USD'))
                    total_amount_eur = total_amount_usd / exchange_rate

                messages.success(request,
                    f'{purchase_count} purchase(s) added successfully! Total: €{total_amount_eur:.2f} / ${total_amount_usd:.2f}')
            except json.JSONDecodeError:
                messages.error(request, 'Invalid cart data')
            except Product.DoesNotExist:
                messages.error(request, 'One or more products not found')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        else:
            messages.error(request, 'Please add products to the cart before completing the purchase')
            return redirect('product:add_purchase_generic')

        return redirect('product:sales_list')


class SalesListView(LoginRequiredMixin, ListView):
    model = Purchase
    template_name = 'product/sales_list.html'
    context_object_name = 'purchases'
    paginate_by = 50

    def get_queryset(self):
        sort = self.request.GET.get('sort', 'date_desc')
        order_map = {
            'date_asc': 'created_at',
            'date_desc': '-created_at',
            'quantity_asc': 'quantity',
            'quantity_desc': '-quantity',
            'total_asc': 'total_price',
            'total_desc': '-total_price',
        }
        order_by = order_map.get(sort, '-created_at')
        qs = Purchase.objects.filter(
            created_by=self.request.user
        ).select_related('client', 'product', 'created_by').annotate(
            total_price=ExpressionWrapper(
                F('quantity') * F('purchase_price'),
                output_field=DecimalField()
            )
        )
        date_from = self.request.GET.get('date_from', '').strip()

        date_to = self.request.GET.get('date_to', '').strip()

        if date_from:
            try:
                qs = qs.filter(created_at__date__gte=date_type.fromisoformat(date_from))
            except ValueError:
                pass
        if date_to:
            try:
                qs = qs.filter(created_at__date__lte=date_type.fromisoformat(date_to))
            except ValueError:
                pass
        return qs.order_by(order_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort'] = self.request.GET.get('sort', 'date_desc')
        context['date_from'] = self.request.GET.get('date_from', '').strip()
        context['date_to'] = self.request.GET.get('date_to', '').strip()

        for key in ('date_from', 'date_to'):
            val = context[key]
            if val:
                try:
                    context[f'{key}_display'] = date_type.fromisoformat(val).strftime('%d.%m.%Y')
                except ValueError:
                    context[f'{key}_display'] = ''
            else:
                context[f'{key}_display'] = ''
        return context


