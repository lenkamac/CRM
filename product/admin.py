from django.contrib import admin
from .models import Product, ProductFile

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'net_price', 'description', 'sold_quantity', 'total_price_display')
    list_filter = ('name',)
    search_fields = ('name',)
    readonly_fields = ('sold_quantity',)  # Make sold_quantity read-only

    def total_price_display(self, obj):
        """Display total price in admin list"""
        return f"${obj.get_total_price():.2f}"

    total_price_display.short_description = 'Total Price'
    total_price_display.admin_order_field = 'net_price'  # Allow sorting by net_price

class ProductFileAdmin(admin.ModelAdmin):
    list_display = ('product', 'file', 'created_at', 'created_by')
    list_filter = ('product',)
    search_fields = ('product__name',)

admin.site.register(Product, ProductAdmin)
admin.site.register(ProductFile, ProductFileAdmin)