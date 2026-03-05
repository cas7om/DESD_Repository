from django import forms
from django.contrib.auth import get_user_model
from config.forms import BootstrapFormMixin
import re

# --- forms config ---

PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")

# Basit doğrulamalar (çok katı yapmadım ki kullanıcıyı bozmasın)
PHONE_REGEX = re.compile(r"^[0-9+\-\s()]{7,20}$")
POSTCODE_REGEX = re.compile(r"^[A-Za-z0-9 ]{3,10}$")

def validate_password_rules(pw: str) -> None:
    """
    TC-022: minimum length + complexity.
    Example rule: >= 8 chars, at least 1 lower, 1 upper, 1 digit.
    """
    if not PASSWORD_REGEX.match(pw or ""):
        raise forms.ValidationError(
            "Password must be at least 8 characters and include an uppercase letter, "
            "a lowercase letter, and a number."
        )

def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()

def _email_exists(email: str) -> bool:
    User = get_user_model()
    try:
        return User.objects.filter(email__iexact=email).exists()
    except Exception:
        # Eğer custom model email alanı farklıysa patlamasın diye
        return False

# ----------------------


class ProducerRegistrationForm(BootstrapFormMixin, forms.Form):
    business_name = forms.CharField(max_length=100)

    contact_name = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=150)
    phone_no = forms.CharField(max_length=20)

    # business address (TC-001 step 6)
    line1 = forms.CharField(max_length=80, label="Business address line 1")
    line2 = forms.CharField(max_length=80, required=False, label="Business address line 2")
    line3 = forms.CharField(max_length=80, required=False, label="Business address line 3")
    postcode = forms.CharField(max_length=10)

    password = forms.CharField(widget=forms.PasswordInput(), validators=[validate_password_rules])
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    accept_terms = forms.BooleanField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # UX: placeholders + autocomplete
        self.fields["business_name"].widget.attrs.update({"placeholder": "e.g. Fresh Farm Ltd", "autocomplete": "organization"})
        self.fields["contact_name"].widget.attrs.update({"placeholder": "e.g. John Doe", "autocomplete": "name"})
        self.fields["email"].widget.attrs.update({"placeholder": "name@email.com", "autocomplete": "email"})
        self.fields["phone_no"].widget.attrs.update({"placeholder": "+44 7xxx xxx xxx", "autocomplete": "tel"})

        self.fields["line1"].widget.attrs.update({"placeholder": "Line 1", "autocomplete": "address-line1"})
        self.fields["line2"].widget.attrs.update({"placeholder": "Line 2 (optional)", "autocomplete": "address-line2"})
        self.fields["line3"].widget.attrs.update({"placeholder": "Line 3 (optional)"})
        self.fields["postcode"].widget.attrs.update({"placeholder": "e.g. BS16 1QY", "autocomplete": "postal-code"})

        self.fields["password"].widget.attrs.update({"autocomplete": "new-password"})
        self.fields["confirm_password"].widget.attrs.update({"autocomplete": "new-password"})

    def clean_email(self):
        email = _normalize_email(self.cleaned_data.get("email"))
        if not email:
            raise forms.ValidationError("Email is required.")
        if _email_exists(email):
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_phone_no(self):
        phone = (self.cleaned_data.get("phone_no") or "").strip()
        if not PHONE_REGEX.match(phone):
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean_postcode(self):
        postcode = (self.cleaned_data.get("postcode") or "").strip().upper()
        if not POSTCODE_REGEX.match(postcode):
            raise forms.ValidationError("Enter a valid postcode.")
        return postcode

    def clean(self):
        cd = super().clean()
        if cd.get("password") and cd.get("confirm_password") and cd["password"] != cd["confirm_password"]:
            raise forms.ValidationError("Passwords do not match.")
        return cd


class CustomerRegistrationForm(BootstrapFormMixin, forms.Form):
    full_name = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=150)
    phone_no = forms.CharField(max_length=20)

    # delivery address (TC-002 step 5-6)
    line1 = forms.CharField(max_length=80, label="Delivery address line 1")
    line2 = forms.CharField(max_length=80, required=False, label="Delivery address line 2")
    line3 = forms.CharField(max_length=80, required=False, label="Delivery address line 3")
    postcode = forms.CharField(max_length=10)

    password = forms.CharField(widget=forms.PasswordInput(), validators=[validate_password_rules])
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    accept_terms = forms.BooleanField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["full_name"].widget.attrs.update({"placeholder": "e.g. Valeria Lanza", "autocomplete": "name"})
        self.fields["email"].widget.attrs.update({"placeholder": "name@email.com", "autocomplete": "email"})
        self.fields["phone_no"].widget.attrs.update({"placeholder": "+44 7xxx xxx xxx", "autocomplete": "tel"})

        self.fields["line1"].widget.attrs.update({"placeholder": "Line 1", "autocomplete": "address-line1"})
        self.fields["line2"].widget.attrs.update({"placeholder": "Line 2 (optional)", "autocomplete": "address-line2"})
        self.fields["line3"].widget.attrs.update({"placeholder": "Line 3 (optional)"})
        self.fields["postcode"].widget.attrs.update({"placeholder": "e.g. BS16 1QY", "autocomplete": "postal-code"})

        self.fields["password"].widget.attrs.update({"autocomplete": "new-password"})
        self.fields["confirm_password"].widget.attrs.update({"autocomplete": "new-password"})

    def clean_email(self):
        email = _normalize_email(self.cleaned_data.get("email"))
        if not email:
            raise forms.ValidationError("Email is required.")
        if _email_exists(email):
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_phone_no(self):
        phone = (self.cleaned_data.get("phone_no") or "").strip()
        if not PHONE_REGEX.match(phone):
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean_postcode(self):
        postcode = (self.cleaned_data.get("postcode") or "").strip().upper()
        if not POSTCODE_REGEX.match(postcode):
            raise forms.ValidationError("Enter a valid postcode.")
        return postcode

    def clean(self):
        cd = super().clean()
        if cd.get("password") and cd.get("confirm_password") and cd["password"] != cd["confirm_password"]:
            raise forms.ValidationError("Passwords do not match.")
        return cd


class AdminRegistrationForm(BootstrapFormMixin, forms.Form):
    full_name = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=150)
    phone_no = forms.CharField(max_length=20)

    password = forms.CharField(widget=forms.PasswordInput(), validators=[validate_password_rules])
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["full_name"].widget.attrs.update({"placeholder": "Full name", "autocomplete": "name"})
        self.fields["email"].widget.attrs.update({"placeholder": "name@email.com", "autocomplete": "email"})
        self.fields["phone_no"].widget.attrs.update({"placeholder": "+44 7xxx xxx xxx", "autocomplete": "tel"})

        self.fields["password"].widget.attrs.update({"autocomplete": "new-password"})
        self.fields["confirm_password"].widget.attrs.update({"autocomplete": "new-password"})

    def clean_email(self):
        email = _normalize_email(self.cleaned_data.get("email"))
        if not email:
            raise forms.ValidationError("Email is required.")
        if _email_exists(email):
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_phone_no(self):
        phone = (self.cleaned_data.get("phone_no") or "").strip()
        if not PHONE_REGEX.match(phone):
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean(self):
        cd = super().clean()
        if cd.get("password") and cd.get("confirm_password") and cd["password"] != cd["confirm_password"]:
            raise forms.ValidationError("Passwords do not match.")
        return cd


class LoginForm(BootstrapFormMixin, forms.Form):
    email = forms.EmailField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput())
    remember_me = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({"placeholder": "name@email.com", "autocomplete": "email"})
        self.fields["password"].widget.attrs.update({"autocomplete": "current-password"})

    def clean_email(self):
        return _normalize_email(self.cleaned_data.get("email"))