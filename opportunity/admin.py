from django.contrib import admin
from .models import Opportunity, Comment


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'account', 'stage', 'amount', 'currency', 'probability', 'expected_close_date', 'assigned_to', 'created_by', 'created_at')
    list_filter = ('stage', 'type', 'lead_source', 'forecast_category', 'currency')
    search_fields = ('name', 'account__company', 'campaign')
    date_hierarchy = 'created_at'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('opportunity', 'created_by', 'created_at')
