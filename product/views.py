from multiprocessing import context
from datetime import date as date_type
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, ExpressionWrapper, DecimalField, F
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from client.models import Purchase
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
        context['purchases'] = self.object.purchases.all().select_related('client', 'created_by')
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


class SalesListView(LoginRequiredMixin, ListView):
    model = Purchase
    template_name = 'product/sales_list.html'
    context_object_name = 'purchases'

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


