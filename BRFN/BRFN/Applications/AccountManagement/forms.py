from django import forms
from django.core.exceptions import ValidationError
from .models import User

class UserForm(forms.ModelForm):
    """
    UserForm - Demonstrates basic ModelForm usage
    """
    # Optional: Override field to add custom widget or validation
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'address'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+44 7XXX XXXXXX'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Full address'
            })
        }

    def clean_email(self):
        """
        Custom validation for email field
        Demonstrates field-level validation
        """
        email = self.cleaned_data.get('email')

        # Check if email already exists (excluding current instance in edit mode)
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('A user with this email already exists.')

        return email.lower()  # Normalise email to lowercase

    def clean_phone(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove spaces and common separators
            phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if not phone.isdigit() or len(phone) < 10:
                raise ValidationError('Please enter a valid phone number (minimum 10 digits)')
        return phone