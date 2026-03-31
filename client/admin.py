from django.contrib import admin
from .models import Client, ClientFile, Comment, Purchase


# Register your models here.
class ClientAdmin(admin.ModelAdmin):
    list_display = ('company', 'last_name', 'first_name', 'email', 'phone', 'mobile', 'created_at', 'status', 'is_converted')
    list_filter = ('created_at', 'status', 'last_name', 'company')
    search_fields = ('last_name', 'email', 'company')

    ordering = ('-created_at',)

    def is_converted(self, obj):
        return obj.converted_from_lead is not None
    is_converted.boolean = True
    is_converted.short_description = 'Converted from lead'

class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('client', 'product', 'quantity', 'purchase_price', 'currency', 'total', 'notes')
    list_filter = ('client', 'product', 'currency')
    search_fields = ('client__company', 'product__name')


admin.site.register(Client, ClientAdmin)
admin.site.register(Comment)
admin.site.register(ClientFile)
admin.site.register(Purchase, PurchaseAdmin)