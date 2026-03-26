
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from product.models import Product
from django.views.generic import ListView, DetailView


# Create your views here.
class ProductListView(ListView):
    model = Product

    template_name = 'product/products-list.html'
    context_object_name = 'products'
    ordering = ['-id']


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'product/product-detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all purchases for this product
        context['purchases'] = self.object.purchases.all().select_related('client', 'created_by')
        return context


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
            description=description
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
    results = []
    if query:
        products = Product.objects.filter(
            name__icontains=query
        ).values('id', 'name', 'net_price')[:10]
        for product in products:
            results.append({
                'id': product['id'],
                'label': product['name'],
            })
    return JsonResponse(results, safe=False)