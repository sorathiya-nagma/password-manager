from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from security.models import UserSecurityProfile
from vault.models import VaultEntry


class Command(BaseCommand):
    help = 'Create a demo user and sample encrypted password entries.'

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username='demo',
            defaults={'email': 'demo@example.com'},
        )
        if created:
            user.set_password('DemoPass123!')
            user.save()
        UserSecurityProfile.objects.get_or_create(user=user)

        samples = [
            {
                'title': 'GitHub',
                'website': 'https://github.com',
                'username': 'demo-dev',
                'email': 'demo@example.com',
                'password': 'GitHub-Demo-99!',
                'category': 'Work',
                'tags': 'code,git',
                'favorite': True,
            },
            {
                'title': 'Bank Portal',
                'website': 'https://bank.example.com',
                'username': 'demo',
                'email': 'demo@example.com',
                'password': 'Banking-Vault-2026!',
                'category': 'Finance',
                'tags': 'money,important',
                'favorite': True,
            },
            {
                'title': 'Old Forum',
                'website': 'https://forum.example.com',
                'username': 'demo_forum',
                'email': 'demo@example.com',
                'password': 'abc',
                'category': 'Personal',
                'tags': 'legacy',
                'favorite': False,
            },
        ]

        for sample in samples:
            entry, _ = VaultEntry.objects.get_or_create(
                owner=user,
                title=sample['title'],
                defaults={
                    'website': sample['website'],
                    'category': sample['category'],
                    'tags': sample['tags'],
                    'favorite': sample['favorite'],
                },
            )
            entry.username = sample['username']
            entry.email = sample['email']
            entry.password = sample['password']
            entry.notes = 'Sample data for local development.'
            entry.save()

        self.stdout.write(self.style.SUCCESS('Sample user created: demo / DemoPass123!'))
