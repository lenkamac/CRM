import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, DeleteView, UpdateView

from client.forms import AddCommentForm, AddFileForm, PurchaseForm
from client.models import Client, Comment, ClientFile, Purchase
from product.models import Product
from task.models import Task
from core.currency_service import CurrencyConverter
import json


# Create your views here.
# Client list
class ClientListView(ListView):
    model = Client
    paginate_by = 10

    def get_queryset(self):
        queryset = super(ClientListView, self).get_queryset()
        queryset = queryset.filter(created_by=self.request.user)

        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(last_name__icontains=query) |
                Q(company__icontains=query) |
                Q(email__icontains=query)
            )

        # Handle sorting
        sort = self.request.GET.get('sort', '-created_at')  # Default: newest first
        queryset = queryset.order_by(sort)

        return queryset


# Client detail page
class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AddCommentForm()
        context['fileform'] = AddFileForm()

        comment_list = Comment.objects.filter(client_id=self.kwargs.get('pk')).order_by('-created_at')
        comment_paginator = Paginator(comment_list, 5)
        comment_page_number = self.request.GET.get('comment_page')
        comments_page = comment_paginator.get_page(comment_page_number)

        task_list = Task.objects.filter(client_id=self.kwargs.get('pk')).order_by('-created_at')
        task_paginator = Paginator(task_list, 8)  # 10 tasks per page
        task_page_number = self.request.GET.get('task_page')
        tasks_page = task_paginator.get_page(task_page_number)

        # Add purchases with filtering
        purchase_list = Purchase.objects.filter(client_id=self.kwargs.get('pk')).select_related('product').order_by(
            '-created_at')

        purchase_product = self.request.GET.get('purchase_product', '').strip()
        purchase_currency = self.request.GET.get('purchase_currency', '').strip()
        purchase_date_from = self.request.GET.get('purchase_date_from', '').strip()
        purchase_date_to = self.request.GET.get('purchase_date_to', '').strip()

        if purchase_product:
            purchase_list = purchase_list.filter(product__name__icontains=purchase_product)
        if purchase_currency:
            purchase_list = purchase_list.filter(currency=purchase_currency)
        if purchase_date_from:
            purchase_list = purchase_list.filter(created_at__date__gte=purchase_date_from)
        if purchase_date_to:
            purchase_list = purchase_list.filter(created_at__date__lte=purchase_date_to)

        purchase_paginator = Paginator(purchase_list, 10)
        purchase_page_number = self.request.GET.get('purchase_page')
        purchases_page = purchase_paginator.get_page(purchase_page_number)

        context['comments'] = comments_page
        context['tasks'] = tasks_page
        context['purchases'] = purchases_page
        context['purchase_filter'] = {
            'product': purchase_product,
            'currency': purchase_currency,
            'date_from': purchase_date_from,
            'date_to': purchase_date_to,
        }
        context['purchase_currency_choices'] = Purchase.CURRENCY_CHOICES

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Let other POST handlers continue (comments, files, etc.)
        return super().get(request, *args, **kwargs)


    def get_queryset(self):
        queryset = super(ClientDetailView, self).get_queryset()
        return queryset.filter(created_by=self.request.user, pk=self.kwargs.get('pk'))


# Comment view
class AddCommentView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pk = kwargs.get('pk')

        form = AddCommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.created_by = request.user
            comment.client_id = pk
            comment.save()
            messages.success(request, "Comment added successfully.")
        else:
            messages.error(request, "Failed to add comment. Please try again.")

        return redirect('client:detail', pk=pk)


# File view
class AddFileView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pk = kwargs.get('pk')

        form = AddFileForm(request.POST, request.FILES)

        if form.is_valid():
            file = form.save(commit=False)
            file.client_id = pk
            file.created_by = request.user
            file.save()

        return redirect('client:detail', pk=pk)


# Create a new client
class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    success_url = reverse_lazy('client:list')
    fields = ('company', 'first_name', 'last_name','phone', 'mobile', 'address', 'zipcode', 'city', 'country', 'email', 'description',
                  'status', 'website',)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        self.object.save()

        return redirect(self.get_success_url())


# Delete client from his detail page
class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    success_url = reverse_lazy('client:list')

    def get_queryset(self):
        queryset = super(ClientDeleteView, self).get_queryset()
        return queryset.filter(created_by=self.request.user, pk=self.kwargs.get('pk'))

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


# Update client
class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Client'
        return context

    fields = ('company', 'first_name', 'last_name', 'phone','mobile','email', 'address', 'zipcode', 'city', 'country', 'description',
              'status', 'website',)
    success_url = reverse_lazy('client:list')

    def get_queryset(self):
        queryset = super(ClientUpdateView, self).get_queryset()
        return queryset.filter(created_by=self.request.user, pk=self.kwargs.get('pk'))


# Export leads in csv
@login_required
def clients_export(request):
    clients =Client.objects.filter(created_by=request.user)

    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="clients.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow(['Last name', 'First name', 'Phone', 'Email', 'Description', 'Created at', 'Created by'])

    for client in clients:
        writer.writerow([client.last_name, client.first_name, client.phone, client.email, client.description,
                         client.created_at, client.created_by])

    return response


# Bulk delete clients
@login_required
def clients_bulk_delete(request):
    if request.method == "POST":
        client_ids = request.POST.getlist("client_ids")  # Get selected lead IDs as a list
        selected_clients = request.POST.getlist('client_ids')

        if client_ids:
            # Delete leads that belong to the requesting user
            Client.objects.filter(id__in=client_ids, created_by=request.user).delete()

            messages.success(request, 'Selected clients were deleted successfully.')
        elif selected_clients:
            Client.objects.filter(id__in=selected_clients).delete()
            messages.success(request, 'Selected clients have been deleted successfully.')
        else:
            messages.warning(request, 'No clients were selected.')

    return redirect('client:list')

# Delete client comment
@login_required
def delete_client_comment(request, client_id, comment_id):
    client = get_object_or_404(Client, id=client_id)
    comment = get_object_or_404(Comment, id=comment_id, client=client)

    # Optional: Only allow the creator of the comment or an admin to delete it
    if request.user == comment.created_by or request.user.is_staff:
        comment.delete()
        messages.success(request, "Comment deleted successfully.")
    else:
        messages.error(request, "You do not have permission to delete this comment.")

    return redirect('client:detail', pk=client.id)

# Edit Comment View
class EditCommentView(LoginRequiredMixin, View):
    def post(self, request, client_id, comment_id):
        client = get_object_or_404(Client, id=client_id)
        comment = get_object_or_404(Comment, id=comment_id, client=client)

        # Restrict to the owner or an admin
        if request.user != comment.created_by and not request.user.is_staff:
            return HttpResponseForbidden("You are not authorized to edit this comment.")

        # Update the comment
        content = request.POST.get("content")
        if content:
            comment.content = content
            comment.save()
            messages.success(request, "Comment updated successfully.")
        else:
            messages.error(request, "Content cannot be empty.")

        return redirect('client:detail', pk=client_id)

# Delete lead file
def delete_client_file(request, client_id, file_id):
    if request.method == "POST":
        client = get_object_or_404(Client, id=client_id)
        file_instance = get_object_or_404(ClientFile, id=file_id, client=client)
        file_instance.delete()
        messages.success(request, "File deleted successfully.")
    return redirect('client:detail', pk=client_id)


# Add purchase page (separate window)
class AddPurchaseView(LoginRequiredMixin, View):
    def get(self, request, pk):
        client = get_object_or_404(Client, pk=pk, created_by=request.user)
        purchaseform = PurchaseForm()

        products = Product.objects.all().values('id', 'name', 'net_price')
        products_dict = {str(p['id']): str(p['net_price']) for p in products}

        try:
            exchange_rate = float(CurrencyConverter.get_exchange_rate('EUR', 'USD'))
        except Exception:
            exchange_rate = 1.10

        return render(request, 'client/add_purchase.html', {
            'client': client,
            'purchaseform': purchaseform,
            'products_json': json.dumps(products_dict),
            'exchange_rate': json.dumps(exchange_rate),
        })

    def post(self, request, pk):
        client = get_object_or_404(Client, pk=pk, created_by=request.user)
        cart_data = request.POST.get('cart_data', '')
        general_notes = request.POST.get('notes', '')

        if cart_data and cart_data != '':
            try:
                cart_items = json.loads(cart_data)

                if len(cart_items) == 0:
                    messages.error(request, 'Please add at least one product to the cart')
                    return redirect('client:add_purchase', pk=pk)

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
                        created_by=request.user
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
            return redirect('client:add_purchase', pk=pk)

        return redirect('client:detail', pk=pk)


# Get exchange rate API endpoint
@login_required
def get_exchange_rate(request):
    """API endpoint to get real-time exchange rate"""
    from_currency = request.GET.get('from', 'EUR')
    to_currency = request.GET.get('to', 'USD')

    rate = float(CurrencyConverter.get_exchange_rate(from_currency, to_currency))

    return JsonResponse({
        'from': from_currency,
        'to': to_currency,
        'rate': rate
    })


@login_required
def client_autocomplete(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        clients = Client.objects.filter(
            created_by=request.user
        ).filter(
            Q(first_name__istartswith=query) |
            Q(last_name__istartswith=query) |
            Q(company__istartswith=query) |
            Q(email__istartswith=query)
        ).values('id', 'first_name', 'last_name', 'company', 'email')[:]
        for client in clients:
            if client['last_name']:
                label = f"{client['last_name']} {client['first_name']}".strip()
            if client['company']:
                label = f"{client['company']}"
            if client['last_name'] and client['company']:
                label = f"{client['company']}, {client['first_name']} {client['last_name']}".strip()
            results.append({'id': client['id'], 'label': label, 'email': client['email']})
    return JsonResponse(results, safe=False)

