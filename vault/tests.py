from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import VaultEntry


class VaultEntryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ada', password='correct-horse-battery-staple')
        self.other_user = User.objects.create_user(username='grace', password='correct-horse-battery-staple')

    def test_saved_secrets_are_encrypted(self):
        entry = VaultEntry(owner=self.user, title='Email')
        entry.username = 'ada@example.com'
        entry.password = 'plain-password'
        entry.notes = 'recovery codes'
        entry.save()

        stored = VaultEntry.objects.get(pk=entry.pk)
        self.assertNotIn('plain-password', stored.encrypted_password)
        self.assertEqual(stored.password, 'plain-password')
        self.assertEqual(stored.username, 'ada@example.com')
        self.assertEqual(stored.notes, 'recovery codes')

    def test_user_cannot_view_another_users_entry(self):
        entry = VaultEntry(owner=self.other_user, title='Bank')
        entry.password = 'secret'
        entry.save()

        self.client.login(username='ada', password='correct-horse-battery-staple')
        response = self.client.get(reverse('vault:detail', args=[entry.pk]))

        self.assertEqual(response.status_code, 404)

    def test_create_entry_requires_login(self):
        response = self.client.get(reverse('vault:create'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_weak_password_shows_strength_guidance(self):
        self.client.login(username='ada', password='correct-horse-battery-staple')

        response = self.client.post(
            reverse('vault:create'),
            {
                'title': 'Weak',
                'website': '',
                'username': 'ada',
                'password': 'abc',
                'notes': '',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Increase password length')
        self.assertContains(response, 'Add a number')
