from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.views import audit

from .forms import CsvImportForm, EncryptedBackupForm, PasswordGeneratorForm, VaultEntryForm, generate_password
from .models import VaultEntry
from .services import (
    apply_vault_filters,
    entries_to_csv,
    entries_to_encrypted_json,
    health_for_entry,
    import_csv,
    mark_viewed,
    restore_encrypted_json,
    visible_entries,
)


@login_required
def entry_list(request):
    entries = apply_vault_filters(visible_entries(request.user), request.GET)
    paginator = Paginator(entries, 9)
    page = paginator.get_page(request.GET.get('page'))
    categories = visible_entries(request.user).exclude(category='').values_list('category', flat=True).distinct()
    return render(
        request,
        'vault/entry_list.html',
        {
            'page': page,
            'entries': page.object_list,
            'categories': categories,
        },
    )


@login_required
def entry_create(request):
    initial = {}
    if request.GET.get('generate') == '1':
        initial['password'] = generate_password()

    form = VaultEntryForm(request.POST or None, owner=request.user, initial=initial)
    if request.method == 'POST' and form.is_valid():
        entry = form.save()
        audit(request.user, 'vault_entry_created', request, entry_id=entry.pk)
        messages.success(request, 'Vault item encrypted and saved.')
        return redirect('vault:list')

    return render(request, 'vault/entry_form.html', {'form': form, 'mode': 'Add'})


@login_required
def entry_update(request, pk):
    entry = get_object_or_404(VaultEntry, pk=pk, owner=request.user)
    form = VaultEntryForm(request.POST or None, instance=entry, owner=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        audit(request.user, 'vault_entry_updated', request, entry_id=entry.pk)
        messages.success(request, 'Vault item updated.')
        return redirect('vault:detail', pk=entry.pk)

    return render(request, 'vault/entry_form.html', {'form': form, 'mode': 'Edit', 'entry': entry})


@login_required
def entry_detail(request, pk):
    entry = get_object_or_404(VaultEntry, pk=pk, owner=request.user)
    mark_viewed(entry)
    return render(request, 'vault/entry_detail.html', {'entry': entry, 'health': health_for_entry(entry)})


@login_required
def reveal_password(request, pk):
    if request.method != 'POST':
        raise Http404
    entry = get_object_or_404(VaultEntry, pk=pk, owner=request.user)
    audit(request.user, 'password_revealed', request, entry_id=entry.pk)
    return JsonResponse({'password': entry.password})


@login_required
def copy_password(request, pk):
    if request.method != 'POST':
        raise Http404
    entry = get_object_or_404(VaultEntry, pk=pk, owner=request.user)
    audit(request.user, 'password_copied', request, entry_id=entry.pk)
    return JsonResponse({'password': entry.password})


@login_required
def entry_delete(request, pk):
    entry = get_object_or_404(VaultEntry, pk=pk, owner=request.user)
    if request.method != 'POST':
        raise Http404
    audit(request.user, 'vault_entry_deleted', request, entry_id=entry.pk)
    entry.delete()
    messages.success(request, 'Vault item deleted.')
    return redirect('vault:list')


@login_required
def generated_password(request):
    form = PasswordGeneratorForm(request.GET or None)
    if form.is_valid():
        password = generate_password(**form.cleaned_data)
    else:
        password = generate_password()
    return JsonResponse({'password': password})


@login_required
def tools(request):
    generator_form = PasswordGeneratorForm(request.GET or None)
    csv_form = CsvImportForm()
    backup_form = EncryptedBackupForm()
    password = ''
    if generator_form.is_valid():
        password = generate_password(**generator_form.cleaned_data)
    return render(
        request,
        'vault/tools.html',
        {
            'generator_form': generator_form,
            'csv_form': csv_form,
            'backup_form': backup_form,
            'generated_password': password,
        },
    )


@login_required
def export_csv(request):
    response = HttpResponse(entries_to_csv(visible_entries(request.user)), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="securevault-{timezone.now().date()}.csv"'
    audit(request.user, 'csv_exported', request)
    return response


@login_required
def export_json(request):
    response = HttpResponse(entries_to_encrypted_json(visible_entries(request.user)), content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="securevault-backup-{timezone.now().date()}.json"'
    audit(request.user, 'encrypted_json_exported', request)
    return response


@login_required
def import_csv_view(request):
    form = CsvImportForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        count = import_csv(request.user, form.cleaned_data['csv_file'])
        audit(request.user, 'csv_imported', request, count=count)
        messages.success(request, f'Imported {count} password item(s).')
    return redirect('vault:tools')


@login_required
def restore_json(request):
    form = EncryptedBackupForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        count = restore_encrypted_json(request.user, form.cleaned_data['backup_file'])
        audit(request.user, 'encrypted_backup_restored', request, count=count)
        messages.success(request, f'Restored {count} password item(s).')
    return redirect('vault:tools')
