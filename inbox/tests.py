import tempfile
from email.message import EmailMessage as PyEmailMessage
from unittest import mock

from django.contrib.auth.models import User
from django.core import mail as django_mail
from django.test import TestCase, override_settings
from django.urls import reverse

from client.models import Client
from .gmail_service import fetch_emails
from .models import Email


def _raw_message(uid):
    msg = PyEmailMessage()
    msg['From'] = 'Jane Doe <jane@example.com>'
    msg['To'] = 'me@gmail.com'
    msg['Subject'] = f'Offer {uid}'
    msg['Date'] = 'Mon, 12 Oct 2026 10:00:00 +0200'
    msg['Message-ID'] = f'<msg-{uid}@example.com>'
    msg.set_content('Hello, here is the offer.')
    msg.add_alternative('<p>Hello, <b>offer</b></p>', subtype='html')
    msg.add_attachment(b'PDFDATA', maintype='application', subtype='pdf', filename='offer.pdf')
    return msg.as_bytes()


class FakeIMAP:
    uids = [1, 2, 3]
    seen = set()

    def __init__(self, host, port=993):
        pass

    def login(self, user, password):
        pass

    def select(self, mailbox, readonly=False):
        pass

    def _flags(self, uid):
        return b'\\Seen' if uid in self.seen else b''

    def uid(self, command, *args):
        if command == 'search':
            return 'OK', [' '.join(str(u) for u in self.uids).encode()]
        if command == 'store':
            uids, op, _ = args
            for uid in map(int, uids.split(',')):
                (FakeIMAP.seen.add if op == '+FLAGS' else FakeIMAP.seen.discard)(uid)
            return 'OK', [None]
        if args[1] == '(FLAGS)':
            return 'OK', [b'%d (UID %d FLAGS (%s))' % (u, u, self._flags(u)) for u in self.uids]
        uid = int(args[0])
        header = b'%d (UID %d FLAGS (%s) BODY[] {1}' % (uid, uid, self._flags(uid))
        return 'OK', [(header, _raw_message(uid)), b')']

    def logout(self):
        pass


@override_settings(MAIL_USER='me@gmail.com', MAIL_PASSWORD='secret', MEDIA_ROOT=tempfile.mkdtemp(),
                   EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class InboxTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('lenka', password='pw')
        self.client_obj = Client.objects.create(email='jane@example.com', last_name='Doe', created_by=self.user)
        self.client.login(username='lenka', password='pw')
        FakeIMAP.seen = set()

    @mock.patch('inbox.gmail_service.imaplib.IMAP4_SSL', FakeIMAP)
    def test_fetch_parses_links_and_deduplicates(self):
        self.assertEqual(fetch_emails(self.user), 3)
        mail = Email.objects.get(imap_uid=2)
        self.assertEqual(mail.sender_email, 'jane@example.com')
        self.assertEqual(mail.sender_name, 'Jane Doe')
        self.assertIn('offer', mail.body_text)
        self.assertIn('<b>offer</b>', mail.body_html)
        self.assertEqual(mail.client, self.client_obj)
        self.assertEqual(mail.attachments.get().filename, 'offer.pdf')
        # Second sync only fetches UIDs above the last stored one
        self.assertEqual(fetch_emails(self.user), 0)

    @mock.patch('inbox.gmail_service.imaplib.IMAP4_SSL', FakeIMAP)
    def test_list_detail_and_unread(self):
        fetch_emails(self.user)
        response = self.client.get(reverse('inbox:list'))
        self.assertContains(response, 'Offer 1')
        self.assertEqual(response.context['inbox_unread_count'], 3)

        mail = Email.objects.get(imap_uid=1)
        response = self.client.get(reverse('inbox:detail', args=[mail.pk]))
        self.assertContains(response, 'offer.pdf')
        mail.refresh_from_db()
        self.assertTrue(mail.is_read)
        # Reading in the CRM marks the message read in Gmail as well
        self.assertEqual(FakeIMAP.seen, {1})
        fetch_emails(self.user)
        mail.refresh_from_db()
        self.assertTrue(mail.is_read)

    @mock.patch('inbox.gmail_service.imaplib.IMAP4_SSL', FakeIMAP)
    def test_read_state_syncs_both_ways(self):
        FakeIMAP.seen = {2}
        fetch_emails(self.user)
        self.assertTrue(Email.objects.get(imap_uid=2).is_read)
        self.assertFalse(Email.objects.get(imap_uid=1).is_read)

        # Changes made in Gmail are picked up on the next sync
        FakeIMAP.seen = {1}
        fetch_emails(self.user)
        self.assertTrue(Email.objects.get(imap_uid=1).is_read)
        self.assertFalse(Email.objects.get(imap_uid=2).is_read)

        # Bulk mark as unread / read in the CRM updates Gmail
        ids = list(Email.objects.values_list('pk', flat=True))
        self.client.post(reverse('inbox:bulk_action'), {'email_ids': ids, 'action': 'read'})
        self.assertEqual(FakeIMAP.seen, {1, 2, 3})
        mail = Email.objects.get(imap_uid=3)
        self.client.post(reverse('inbox:toggle_read', args=[mail.pk]))
        self.assertEqual(FakeIMAP.seen, {1, 2})

    def test_other_users_cannot_see_email(self):
        other = User.objects.create_user('other', password='pw')
        mail = Email.objects.create(owner=other, message_id='<x>', subject='Secret', received_at='2026-10-01T10:00Z')
        response = self.client.get(reverse('inbox:detail', args=[mail.pk]))
        self.assertEqual(response.status_code, 404)

    @mock.patch('inbox.gmail_service.get_connection')
    def test_reply_sends_and_stores_sent_copy(self, get_connection):
        from django.core.mail import get_connection as real_get_connection
        get_connection.return_value = real_get_connection('django.core.mail.backends.locmem.EmailBackend')
        original = Email.objects.create(owner=self.user, message_id='<orig@example.com>', subject='Hi',
                                        sender_email='jane@example.com', received_at='2026-10-01T10:00Z')
        response = self.client.post(reverse('inbox:reply', args=[original.pk]), {
            'to': 'jane@example.com', 'subject': 'Re: Hi', 'body': 'Thanks!',
        })
        self.assertRedirects(response, reverse('inbox:detail', args=[original.pk]))
        self.assertEqual(len(django_mail.outbox), 1)
        self.assertEqual(django_mail.outbox[0].extra_headers['In-Reply-To'], '<orig@example.com>')
        sent = Email.objects.get(folder=Email.SENT)
        self.assertEqual(sent.client, self.client_obj)
        self.assertEqual(sent.in_reply_to, '<orig@example.com>')

    def test_next_redirect_rejects_external_url(self):
        mail = Email.objects.create(owner=self.user, message_id='<y>', received_at='2026-10-01T10:00Z')
        response = self.client.post(reverse('inbox:toggle_star', args=[mail.pk]), {'next': 'https://evil.com/'})
        self.assertRedirects(response, reverse('inbox:list'))
