from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from inbox.gmail_service import MailNotConfigured, fetch_emails


class Command(BaseCommand):
    help = ('Fetch new email messages into the CRM inbox (use from cron for automatic sync). '
            'Pass a username, or --all for every user with a connected mailbox.')

    def add_arguments(self, parser):
        parser.add_argument('username', nargs='?', help='CRM user who owns the inbox')
        parser.add_argument('--all', action='store_true', help='Sync every connected mailbox')

    def handle(self, *args, **options):
        if options['all']:
            users = User.objects.filter(mail_account__is_active=True)
        elif options['username']:
            try:
                users = [User.objects.get(username=options['username'])]
            except User.DoesNotExist:
                raise CommandError(f'User "{options["username"]}" does not exist.')
        else:
            raise CommandError('Give a username or use --all.')

        failed = False
        for user in users:
            try:
                count = fetch_emails(user)
            except MailNotConfigured as e:
                if not options['all']:
                    raise CommandError(str(e))
                self.stderr.write(f'{user.username}: {e}')
                failed = True
            except Exception as e:  # one broken mailbox must not stop the others
                self.stderr.write(self.style.ERROR(f'{user.username}: sync failed: {e}'))
                failed = True
            else:
                self.stdout.write(self.style.SUCCESS(f'{count} new email(s) fetched for {user.username}.'))
        if failed and not options['all']:
            raise CommandError('Sync failed.')
