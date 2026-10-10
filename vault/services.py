import csv
import io
import json

from django.db.models import Q
from django.utils import timezone

from .crypto import decrypt_value, encrypt_value
from .forms import password_strength_issues, password_strength_label
from .models import VaultEntry


def visible_entries(user):
    return VaultEntry.objects.filter(owner=user)


def apply_vault_filters(queryset, params):
    query = params.get('q', '').strip()
    category = params.get('category', '').strip()
    mode = params.get('filter', '').strip()
    sort = params.get('sort', 'newest')

    if query:
        queryset = queryset.filter(
            Q(title__icontains=query)
            | Q(website__icontains=query)
            | Q(category__icontains=query)
            | Q(tags__icontains=query)
        )
    if category:
        queryset = queryset.filter(category__iexact=category)
    if mode == 'favorites':
        queryset = queryset.filter(favorite=True)
    if mode == 'recent':
        queryset = queryset.order_by('-created_at')

    sort_map = {
        'az': 'title',
        'newest': '-created_at',
        'oldest': 'created_at',
    }
    return queryset.order_by(sort_map.get(sort, '-created_at'))


def health_for_entry(entry):
    password = entry.password
    issues = password_strength_issues(password)
    return {
        'label': password_strength_label(password),
        'issues': issues,
    }


def health_summary(entries):
    data = [health_for_entry(entry) for entry in entries]
    total = len(data)
    weak = sum(item['label'] == 'Weak' for item in data)
    score = 100 if not total else round(((total - weak) / total) * 100)
    return {
        'score': score,
        'weak_count': weak,
        'items': data,
    }


def mark_viewed(entry):
    entry.last_viewed_at = timezone.now()
    entry.save(update_fields=['last_viewed_at'])


def entries_to_csv(entries):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['website_name', 'website_url', 'username', 'email', 'password', 'notes', 'category', 'tags'])
    for entry in entries:
        writer.writerow([
            entry.title,
            entry.website,
            entry.username,
            entry.email,
            entry.password,
            entry.notes,
            entry.category,
            entry.tags,
        ])
    return output.getvalue()


def entries_to_encrypted_json(entries):
    payload = []
    for entry in entries:
        payload.append({
            'website_name': entry.title,
            'website_url': entry.website,
            'encrypted_username': entry.encrypted_username,
            'encrypted_email': entry.encrypted_email,
            'encrypted_password': entry.encrypted_password,
            'encrypted_notes': entry.encrypted_notes,
            'category': entry.category,
            'tags': entry.tags,
            'favorite': entry.favorite,
        })
    return json.dumps({'version': 1, 'entries': payload}, indent=2)


def import_csv(user, file_obj):
    decoded = io.TextIOWrapper(file_obj, encoding='utf-8-sig')
    reader = csv.DictReader(decoded)
    created = 0
    for row in reader:
        title = (row.get('website_name') or row.get('title') or '').strip()
        password = (row.get('password') or '').strip()
        if not title or not password:
            continue
        entry = VaultEntry(owner=user, title=title, website=row.get('website_url') or row.get('website') or '')
        entry.username = row.get('username', '')
        entry.email = row.get('email', '')
        entry.password = password
        entry.notes = row.get('notes', '')
        entry.category = row.get('category', '')
        entry.tags = row.get('tags', '')
        entry.save()
        created += 1
    return created


def restore_encrypted_json(user, file_obj):
    data = json.loads(file_obj.read().decode('utf-8'))
    created = 0
    for row in data.get('entries', []):
        entry = VaultEntry.objects.create(
            owner=user,
            title=row.get('website_name', 'Imported item'),
            website=row.get('website_url', ''),
            encrypted_username=row.get('encrypted_username', encrypt_value('')),
            encrypted_email=row.get('encrypted_email', encrypt_value('')),
            encrypted_password=row.get('encrypted_password', ''),
            encrypted_notes=row.get('encrypted_notes', encrypt_value('')),
            category=row.get('category', ''),
            tags=row.get('tags', ''),
            favorite=bool(row.get('favorite')),
        )
        if not decrypt_value(entry.encrypted_password):
            entry.delete()
            continue
        created += 1
    return created
