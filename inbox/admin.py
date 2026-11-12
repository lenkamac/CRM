from django.contrib import admin
from .models import Email, EmailAttachment, MailAccount


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


class MailAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_address', 'imap_host', 'smtp_host', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('user__username', 'email_address')
    # The encrypted password is never shown or edited here - users set it in Inbox -> Settings
    exclude = ('password_encrypted',)


admin.site.register(MailAccount, MailAccountAdmin)
