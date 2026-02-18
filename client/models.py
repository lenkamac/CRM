from django.db import models
from django.contrib.auth.models import User
from lead.models import Lead
from product.models import Product

# Create your models here.
class Client(models.Model):
    resale = 'resale'
    direct = 'direct'

    CHOICES_STATUS = (
        (resale, 'Resale'),
        (direct, 'Direct'),
    )

    status = models.CharField(max_length=255, choices=CHOICES_STATUS, default='', blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    zipcode = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    due_time = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='clients', on_delete=models.CASCADE)
    modified_at = models.DateTimeField(auto_now=True)
    converted_from_lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name="converted_client")


    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.last_name or self.first_name:
            name_parts = [self.last_name, self.first_name]
            name = ' '.join(filter(None, name_parts))
            if self.company:
                return f'{name} - {self.company}'
            return name
        return self.company or 'Unnamed Client'

class Comment(models.Model):
    client = models.ForeignKey(Client, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='client_comments', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.created_by.username


class ClientFile(models.Model):
    client = models.ForeignKey(Client, related_name='files', on_delete=models.CASCADE)
    file = models.FileField(upload_to='clientfiles')
    created_by = models.ForeignKey(User, related_name='client_files', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.created_by.username


class Purchase(models.Model):
    EUR = 'EUR'
    USD = 'USD'

    CURRENCY_CHOICES = (
        (EUR, '€'),
        (USD, '$'),
    )

    client = models.ForeignKey(Client, related_name='purchases', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='purchases', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Leave empty to use product's net price")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default=EUR)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='client_purchases', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.client} - {self.product.name} ({self.quantity})'

    def get_purchase_price(self):
        """Return purchase price or product's net price if not set"""
        return self.purchase_price if self.purchase_price else self.product.net_price

    @property
    def total(self):
        """Calculate total price"""
        return self.quantity * self.get_purchase_price()

    def save(self, *args, **kwargs):
        # Set purchase_price to product's net_price if not provided
        if self.purchase_price is None:
            self.purchase_price = self.product.net_price

        # Only track sold items on creation
        if not self.pk:
            self.product.sold_quantity += self.quantity
            self.product.save()

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
