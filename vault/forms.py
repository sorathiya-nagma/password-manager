import secrets
import string

from django import forms

from .models import VaultEntry

MIN_PASSWORD_LENGTH = 12
SPECIAL_CHARACTERS = '!@#$%^&*()-_=+[]{}'


class VaultEntryForm(forms.ModelForm):
    username = forms.CharField(max_length=180, required=False)
    email = forms.EmailField(required=False)
    password = forms.CharField(widget=forms.PasswordInput(render_value=True))
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)

    class Meta:
        model = VaultEntry
        fields = (
            'title',
            'website',
            'username',
            'email',
            'password',
            'notes',
            'category',
            'tags',
            'favorite',
            'expires_at',
        )
        widgets = {
            'expires_at': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner', None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.username
            self.fields['email'].initial = self.instance.email
            self.fields['password'].initial = self.instance.password
            self.fields['notes'].initial = self.instance.notes

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        queryset = VaultEntry.objects.filter(owner=self.owner, title__iexact=title)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('You already have a vault item with this title.')
        return title

    def clean_password(self):
        password = self.cleaned_data['password']
        issues = password_strength_issues(password)
        if issues:
            raise forms.ValidationError(' '.join(issues))
        return password

    def save(self, commit=True):
        entry = super().save(commit=False)
        if self.owner is not None:
            entry.owner = self.owner
        entry.username = self.cleaned_data.get('username', '')
        entry.email = self.cleaned_data.get('email', '')
        entry.password = self.cleaned_data['password']
        entry.notes = self.cleaned_data.get('notes', '')
        if commit:
            entry.save()
        return entry


class PasswordGeneratorForm(forms.Form):
    length = forms.IntegerField(min_value=8, max_value=128, initial=20)
    uppercase = forms.BooleanField(required=False, initial=True)
    lowercase = forms.BooleanField(required=False, initial=True)
    numbers = forms.BooleanField(required=False, initial=True)
    symbols = forms.BooleanField(required=False, initial=True)
    exclude_similar = forms.BooleanField(required=False, initial=True)


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


class EncryptedBackupForm(forms.Form):
    backup_file = forms.FileField()


def generate_password(
    length=20,
    uppercase=True,
    lowercase=True,
    numbers=True,
    symbols=True,
    exclude_similar=False,
):
    groups = []
    if uppercase:
        groups.append(string.ascii_uppercase)
    if lowercase:
        groups.append(string.ascii_lowercase)
    if numbers:
        groups.append(string.digits)
    if symbols:
        groups.append(SPECIAL_CHARACTERS)
    if not groups:
        groups = [string.ascii_letters + string.digits]

    alphabet = ''.join(groups)
    if exclude_similar:
        for char in 'Il1O0':
            alphabet = alphabet.replace(char, '')

    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        if not password_strength_issues(password):
            return password


def password_strength_issues(password):
    issues = []
    if len(password) < MIN_PASSWORD_LENGTH:
        issues.append(f'Increase password length to at least {MIN_PASSWORD_LENGTH} characters.')
    if not any(char.islower() for char in password):
        issues.append('Add a lowercase letter.')
    if not any(char.isupper() for char in password):
        issues.append('Add an uppercase letter.')
    if not any(char.isdigit() for char in password):
        issues.append('Add a number.')
    if not any(char in SPECIAL_CHARACTERS for char in password):
        issues.append('Add a special character.')
    return issues


def password_strength_label(password):
    score = 0
    score += len(password) >= MIN_PASSWORD_LENGTH
    score += len(password) >= 16
    score += any(char.islower() for char in password)
    score += any(char.isupper() for char in password)
    score += any(char.isdigit() for char in password)
    score += any(char in SPECIAL_CHARACTERS for char in password)
    if score <= 2:
        return 'Weak'
    if score <= 4:
        return 'Medium'
    if score == 5:
        return 'Strong'
    return 'Very Strong'
