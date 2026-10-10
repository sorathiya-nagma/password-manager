from collections import Counter

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from security.models import AuditLog, LoginAttempt
from vault.services import health_for_entry, health_summary, visible_entries


@login_required
def home(request):
    entries = list(visible_entries(request.user))
    categories = Counter(entry.category or 'Uncategorized' for entry in entries)
    favorites = [entry for entry in entries if entry.favorite]
    recent = sorted(entries, key=lambda entry: entry.created_at, reverse=True)[:5]
    health = health_summary(entries)
    weak_entries = [entry for entry in entries if health_for_entry(entry)['label'] == 'Weak']
    password_counts = Counter(entry.password for entry in entries)
    reused = [entry for entry in entries if password_counts[entry.password] > 1]
    login_history = LoginAttempt.objects.filter(username=request.user.username)[:5]
    audit_logs = AuditLog.objects.filter(user=request.user)[:8]

    return render(
        request,
        'dashboard/home.html',
        {
            'total_passwords': len(entries),
            'recent_entries': recent,
            'category_counts': list(categories.items()),
            'favorite_count': len(favorites),
            'health': health,
            'weak_entries': weak_entries,
            'reused_entries': reused,
            'login_history': login_history,
            'audit_logs': audit_logs,
        },
    )
