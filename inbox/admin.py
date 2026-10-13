from django.contrib import admin
from .models import Email, EmailAttachment


# Register your models here.
class EmailAttachmentInline(admin.TabularInline):
    model = EmailAttachment
    extra = 0


class EmailAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender_email', 'to', 'folder', 'received_at', 'is_read', 'is_starred', 'owner')
    list_filter = ('folder', 'is_read', 'is_starred', 'received_at')
    search_fields = ('subject', 'sender_email', 'sender_name', 'to')
    ordering = ('-received_at',)
    inlines = [EmailAttachmentInline]


admin.site.register(Email, EmailAdmin)
