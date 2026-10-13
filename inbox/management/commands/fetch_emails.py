from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from inbox.gmail_service import MailNotConfigured, fetch_emails


class Command(BaseCommand):
    help = 'Fetch new email messages into the CRM inbox of the given user (use from cron for automatic sync).'

    def add_arguments(self, parser):
        parser.add_argument('username', help='CRM user who owns the inbox')

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options['username'])
        except User.DoesNotExist:
            raise CommandError(f'User "{options["username"]}" does not exist.')
        try:
            count = fetch_emails(user)
        except MailNotConfigured as e:
            raise CommandError(str(e))
        self.stdout.write(self.style.SUCCESS(f'{count} new email(s) fetched for {user.username}.'))
