"""Work out who an email is really from, so the CRM can prefill a lead/client.

For a normal email that is the From header. For a forwarded email the From
header is the person who forwarded it, so we look inside the body for the
original "From:" block that Gmail, Outlook, Apple Mail, Seznam, ... insert.
"""
import html
import re
from email.utils import parseaddr

# Subject prefixes used for forwards in common languages (Fwd, FW, WG, TR, PŘ, ...)
FORWARD_SUBJECT_RE = re.compile(r'^\s*(?:(?:fwd?|fw|wg|tr|rv|enc|vs|př|přep|doorst)\s*:\s*)+', re.IGNORECASE)

# Lines that start a forwarded part of a message. "Strong" markers are only used for
# forwards; "weak" ones (Outlook) are also used when quoting a reply.
STRONG_MARKER_RE = re.compile(
    r'^[\s>*_-]*(?:'
    # Text may follow the keyword, e.g. '---- Weitergeleitete Nachricht von "Name" <a@b.de> ---'
    r'-+\s*(?:forwarded message|přeposlaná zpráva|weitergeleitete nachricht|message transféré)\b[^\n]*'
    r'|begin forwarded message:?'
    r')[ \t]*$',
    re.IGNORECASE | re.MULTILINE,
)
WEAK_MARKER_RE = re.compile(
    r'^[\s>*_-]*(?:'
    r'-+\s*(?:original message|původní zpráva|ursprüngliche nachricht|message d\'origine)\b[^\n]*'
    r'|_{5,}'
    r')[ \t]*$',
    re.IGNORECASE | re.MULTILINE,
)

# "From: Jane Doe <jane@example.com>" / "Od: ..." / "Von: ..." / "De : ..."
FROM_LINE_RE = re.compile(r'^[\s>]*\**\s*(?:from|od|von|de|van|da)\s*:\s*\**\s*(.+)$', re.IGNORECASE | re.MULTILINE)

EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+')

# Phone: optional +/00 prefix, digits separated by spaces, dashes, slashes or parentheses
PHONE_RE = re.compile(r'(?<![\w.:])(?:\+|00)?\(?\d[\d\s\-/()]{7,}\d(?![\w.:])')
PHONE_LABEL_RE = re.compile(r'(?:tel|phone|mobil|mobile|mob|cell|telefon|gsm)\.?\s*[:.]?\s*', re.IGNORECASE)


def html_to_text(value):
    value = re.sub(r'(?is)<(script|style).*?</\1>', '', value)
    value = re.sub(r'(?i)<br\s*/?>|</(p|div|tr|li|h\d)>', '\n', value)
    value = re.sub(r'<[^>]+>', '', value)
    return html.unescape(value)


def _body_text(mail):
    return mail.body_text or html_to_text(mail.body_html or '')


def _parse_from(value):
    """Parse 'Jane Doe <jane@x.com>', 'Jane Doe [mailto:jane@x.com]', 'jane@x.com' etc."""
    value = value.replace('mailto:', '').replace('[', '<').replace(']', '>').strip().strip('*').strip()
    name, address = parseaddr(value)
    if not address or '@' not in address:
        found = EMAIL_RE.search(value)
        if not found:
            return '', ''
        address = found.group(0)
        name = value[:found.start()]
    name = name.strip(' "\'<>*,')
    if name.lower() == address.lower():
        name = ''
    return name, address


def split_name(full_name):
    """'Jane Doe' -> ('Jane', 'Doe'); 'Doe, Jane' -> ('Jane', 'Doe')."""
    full_name = ' '.join(full_name.split())
    if not full_name:
        return '', ''
    if ',' in full_name:
        last, first = [p.strip() for p in full_name.split(',', 1)]
        return first, last
    parts = full_name.split(' ')
    if len(parts) == 1:
        return '', parts[0]
    return ' '.join(parts[:-1]), parts[-1]


def find_phone(text):
    """Return the first phone number in text, preferring ones with a 'Tel:'/'Mobile:' label."""
    candidates = []
    for line in text.splitlines():
        line = line.lstrip('> ')
        for match in PHONE_RE.finditer(line):
            number = ' '.join(match.group(0).split()).strip()
            digits = re.sub(r'\D', '', number)
            if not 9 <= len(digits) <= 15:
                continue
            labelled = bool(PHONE_LABEL_RE.search(line[:match.start()]))
            candidates.append((not labelled, number))
    if not candidates:
        return ''
    candidates.sort(key=lambda c: c[0])  # stable: labelled numbers first, otherwise original order
    return candidates[0][1]


def _first_from(body, start, end, exclude):
    """First usable 'From:' line in body[start:end] -> (name, email, position) or None."""
    for match in FROM_LINE_RE.finditer(body, start, end):
        name, address = _parse_from(match.group(1))
        if address and address.lower() not in exclude:
            return name, address, match.start()
    return None


def find_forwarded_sender(subject, body, exclude=()):
    """Return (name, email, original_part_of_body) for a forwarded email, or None.

    Handles forward chains (Fw: Fw: Fw:) by taking the deepest forwarded block,
    i.e. the person who wrote the email in the first place. Addresses in
    `exclude` (e.g. your own mailbox) are never returned as the original sender.
    """
    exclude = {a.lower() for a in exclude if a}
    strong = [m.end() for m in STRONG_MARKER_RE.finditer(body)]
    weak = [m.end() for m in WEAK_MARKER_RE.finditer(body)]
    # Prefer strong markers so a reply quoted inside the original email isn't
    # mistaken for another forward; Outlook-only chains fall back to weak ones.
    markers = strong or weak
    if not markers:
        if not FORWARD_SUBJECT_RE.match(subject or ''):
            return None
        markers = [0]
    boundaries = sorted(set(strong + weak + markers)) + [len(body)]

    for marker in reversed(markers):  # deepest block first
        block_end = next((b for b in boundaries if b > marker), len(body))
        found = _first_from(body, marker, block_end, exclude)
        if found:
            name, address, pos = found
            return name, address, body[pos:block_end]
    return None


def original_contact(mail, exclude=()):
    """Details of the real sender of an email: dict with name, email, first_name, last_name, phone, forwarded."""
    body = _body_text(mail)
    forwarded = find_forwarded_sender(mail.subject, body, exclude)
    if forwarded:
        name, address, original_part = forwarded
    else:
        name, address, original_part = mail.sender_name, mail.sender_email, body
    first_name, last_name = split_name(name)
    return {
        'name': name,
        'email': address,
        'first_name': first_name,
        'last_name': last_name,
        'phone': find_phone(original_part),
        'forwarded': bool(forwarded),
    }
