from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView

from security.models import AuditLog, LoginAttempt, UserSecurityProfile
from security.totp import generate_totp_secret, verify_totp
from vault.crypto import decrypt_value, encrypt_value

from .forms import ProfileForm, RegisterForm, SecureLoginForm, TwoFactorVerifyForm


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def audit(user, action, request, **metadata):
    AuditLog.objects.create(
        user=user,
        action=action,
        metadata=metadata,
        ip_address=client_ip(request),
    )


def is_locked(username, ip_address):
    since = timezone.now() - timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
    failures = LoginAttempt.objects.filter(
        username=username,
        ip_address=ip_address,
        successful=False,
        created_at__gte=since,
    ).count()
    return failures >= settings.LOGIN_LOCKOUT_ATTEMPTS


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('dashboard:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        UserSecurityProfile.objects.get_or_create(user=self.object)
        login(self.request, self.object)
        audit(self.object, 'account_registered', self.request)
        messages.success(self.request, 'Your secure vault is ready.')
        return response


class SecureLoginView(LoginView):
    authentication_form = SecureLoginForm
    template_name = 'registration/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            username = request.POST.get('username', '').strip()
            if is_locked(username, client_ip(request)):
                messages.error(request, 'Too many failed attempts. Try again later.')
                return render(request, self.template_name, {'form': self.get_form()})
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        profile, _ = UserSecurityProfile.objects.get_or_create(user=user)
        secret = decrypt_value(profile.encrypted_totp_secret)
        if profile.totp_enabled and not verify_totp(secret, form.cleaned_data.get('otp_code')):
            LoginAttempt.objects.create(
                username=user.username,
                ip_address=client_ip(self.request),
                successful=False,
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            )
            messages.error(self.request, 'Invalid authenticator code.')
            return self.form_invalid(form)

        remember = form.cleaned_data.get('remember_me')
        self.request.session.set_expiry(settings.SESSION_COOKIE_AGE if remember else 0)
        LoginAttempt.objects.create(
            username=user.username,
            ip_address=client_ip(self.request),
            successful=True,
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
        )
        audit(user, 'login_success', self.request)
        return super().form_valid(form)

    def form_invalid(self, form):
        username = self.request.POST.get('username', '').strip()
        LoginAttempt.objects.create(
            username=username,
            ip_address=client_ip(self.request),
            successful=False,
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
        )
        return super().form_invalid(form)


def settings_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile, _ = UserSecurityProfile.objects.get_or_create(user=request.user)
    profile_form = ProfileForm(request.POST or None, instance=request.user)
    totp_form = TwoFactorVerifyForm(request.POST or None, prefix='totp')
    secret = decrypt_value(profile.encrypted_totp_secret)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'profile' and profile_form.is_valid():
            profile_form.save()
            audit(request.user, 'profile_updated', request)
            messages.success(request, 'Profile updated.')
            return redirect('accounts:settings')
        if action == 'dark_mode':
            profile.dark_mode = not profile.dark_mode
            profile.save(update_fields=['dark_mode'])
            return redirect('accounts:settings')
        if action == 'prepare_2fa':
            if not secret:
                secret = generate_totp_secret()
                profile.encrypted_totp_secret = encrypt_value(secret)
                profile.save(update_fields=['encrypted_totp_secret'])
            return redirect('accounts:settings')
        if action == 'enable_2fa' and totp_form.is_valid():
            if verify_totp(secret, totp_form.cleaned_data['otp_code']):
                profile.totp_enabled = True
                profile.save(update_fields=['totp_enabled'])
                audit(request.user, '2fa_enabled', request)
                messages.success(request, 'Two-factor authentication enabled.')
                return redirect('accounts:settings')
            messages.error(request, 'That authenticator code did not match.')
        if action == 'disable_2fa':
            profile.totp_enabled = False
            profile.save(update_fields=['totp_enabled'])
            audit(request.user, '2fa_disabled', request)
            messages.success(request, 'Two-factor authentication disabled.')
            return redirect('accounts:settings')
        if action == 'delete_account':
            audit(request.user, 'account_deleted', request)
            request.user.delete()
            messages.success(request, 'Your account was deleted.')
            return redirect('login')

    return render(
        request,
        'accounts/settings.html',
        {
            'profile_form': profile_form,
            'totp_form': totp_form,
            'profile': profile,
            'totp_secret': secret,
        },
    )
