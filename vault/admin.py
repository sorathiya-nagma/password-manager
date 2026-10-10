from django.contrib import admin

from .models import VaultEntry


@admin.register(VaultEntry)
class VaultEntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'category', 'favorite', 'updated_at')
    list_filter = ('owner', 'category', 'favorite', 'updated_at')
    search_fields = ('title', 'website', 'category', 'tags', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')

# Register your models here.
