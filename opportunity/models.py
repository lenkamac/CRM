from django.db import models
from django.contrib.auth.models import User
from client.models import Client


class Opportunity(models.Model):
    # Sale Stage
    PROSPECTING = 'prospecting'
    QUALIFICATION = 'qualification'
    VALUE_PROPOSITION = 'value_proposition'
    PROPOSAL_PRICE_QUOTE = 'proposal_price_quote'
    NEGOTIATION_REVIEW = 'negotiation_review'
    CLOSED_WON = 'closed_won'
    CLOSED_LOST = 'closed_lost'

    STAGE_CHOICES = (
        (PROSPECTING, 'Prospecting'),
        (QUALIFICATION, 'Qualification'),
        (VALUE_PROPOSITION, 'Value Proposition'),
        (PROPOSAL_PRICE_QUOTE, 'Proposal / Price Quote'),
        (NEGOTIATION_REVIEW, 'Negotiation / Review'),
        (CLOSED_WON, 'Closed Won'),
        (CLOSED_LOST, 'Closed Lost'),
    )

    # Type
    EXISTING_BUSINESS = 'existing_business'
    NEW_BUSINESS = 'new_business'

    TYPE_CHOICES = (
        (EXISTING_BUSINESS, 'Existing Business'),
        (NEW_BUSINESS, 'New Business'),
    )

    # Lead Source
    WEB = 'web'
    PHONE = 'phone'
    EMAIL = 'email'
    COLD_CALL = 'cold_call'
    EXISTING_CUSTOMER = 'existing_customer'
    PARTNER = 'partner'
    TRADE_SHOW = 'trade_show'
    OTHER = 'other'

    LEAD_SOURCE_CHOICES = (
        (WEB, 'Web'),
        (PHONE, 'Phone'),
        (EMAIL, 'Email'),
        (COLD_CALL, 'Cold Call'),
        (EXISTING_CUSTOMER, 'Existing Customer'),
        (PARTNER, 'Partner'),
        (TRADE_SHOW, 'Trade Show'),
        (OTHER, 'Other'),
    )

    # Forecast Category
    PIPELINE = 'pipeline'
    BEST_CASE = 'best_case'
    COMMIT = 'commit'
    OMITTED = 'omitted'
    CLOSED = 'closed'

    FORECAST_CHOICES = (
        (PIPELINE, 'Pipeline'),
        (BEST_CASE, 'Best Case'),
        (COMMIT, 'Commit'),
        (OMITTED, 'Omitted'),
        (CLOSED, 'Closed'),
    )

    # Currency
    EUR = 'EUR'
    USD = 'USD'

    CURRENCY_CHOICES = (
        (EUR, 'EUR (€)'),
        (USD, 'USD ($)'),
    )

    name = models.CharField(max_length=255)
    account = models.ForeignKey(Client, related_name='opportunities', on_delete=models.SET_NULL, null=True, blank=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default=EUR)
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    stage = models.CharField(max_length=50, choices=STAGE_CHOICES, default=PROSPECTING)
    probability = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Probability in %")
    next_step = models.TextField(blank=True, null=True)
    expected_close_date = models.DateField(blank=True, null=True)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, blank=True, null=True)
    lead_source = models.CharField(max_length=50, choices=LEAD_SOURCE_CHOICES, blank=True, null=True)
    campaign = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    assigned_to = models.ForeignKey(User, related_name='assigned_opportunities', on_delete=models.SET_NULL, null=True, blank=True)
    forecast_category = models.CharField(max_length=50, choices=FORECAST_CHOICES, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name='opportunities', on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Comment(models.Model):
    opportunity = models.ForeignKey(Opportunity, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='opportunity_comments', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.created_by.username
