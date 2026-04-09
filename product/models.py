from django.db import models
from decimal import Decimal
from django.contrib.auth.models import User

class Product(models.Model):
    name = models.CharField(max_length=255)
    net_price = models.DecimalField(max_digits=10, decimal_places=2)
    sold_quantity = models.IntegerField(default=0)  # Track total sold
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='products')

    def get_total_price(self):
        """Calculate total revenue from all purchases in EUR"""
        from core.currency_service import CurrencyConverter

        total = Decimal('0.00')
        for purchase in self.purchases.all():
            # Get the purchase price (stored in its original currency)
            base_price = purchase.purchase_price if purchase.purchase_price else self.net_price
            purchase_total = purchase.quantity * base_price

            # Convert USD purchases to EUR
            if purchase.currency == 'USD':
                purchase_total = CurrencyConverter.convert(purchase_total, 'USD', 'EUR')

            total += purchase_total

        return total

    def __str__(self):
        return self.name