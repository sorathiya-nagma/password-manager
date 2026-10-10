from django.conf import settings
from django.db import models
from django.urls import reverse

from .crypto import decrypt_value, encrypt_value


class VaultEntry(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vault_entries',
    )
    title = models.CharField(max_length=120)
    website = models.URLField(blank=True)
    encrypted_username = models.TextField(blank=True)
    encrypted_email = models.TextField(blank=True)
    encrypted_password = models.TextField()
    encrypted_notes = models.TextField(blank=True)
    category = models.CharField(max_length=80, blank=True)
    tags = models.CharField(max_length=255, blank=True)
    favorite = models.BooleanField(default=False)
    last_viewed_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['owner', 'title']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['owner', 'title'], name='unique_vault_title_per_owner'),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('vault:detail', args=[self.pk])

    @property
    def website_name(self):
        return self.title

    @property
    def website_url(self):
        return self.website

    @property
    def username(self):
        return decrypt_value(self.encrypted_username)

    @username.setter
    def username(self, value):
        self.encrypted_username = encrypt_value(value)

    @property
    def email(self):
        return decrypt_value(self.encrypted_email)

    @email.setter
    def email(self, value):
        self.encrypted_email = encrypt_value(value)

    @property
    def password(self):
        return decrypt_value(self.encrypted_password)

    @password.setter
    def password(self, value):
        self.encrypted_password = encrypt_value(value)

    @property
    def notes(self):
        return decrypt_value(self.encrypted_notes)

    @notes.setter
    def notes(self, value):
        self.encrypted_notes = encrypt_value(value)

# Create your models here.
