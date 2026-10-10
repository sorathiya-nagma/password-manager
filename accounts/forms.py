from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class SecureLoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False)
    otp_code = forms.CharField(
        label='Authenticator code',
        max_length=6,
        required=False,
        help_text='Required only when 2FA is enabled.',
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        queryset = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('This email is already in use.')
        return email


class TwoFactorVerifyForm(forms.Form):
    otp_code = forms.CharField(label='Authenticator code', max_length=6)
