from django import forms
from config.forms import BootstrapFormMixin
import re

#--- forms config ---

PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")

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
#------


class ProducerRegistrationForm(BootstrapFormMixin,forms.Form):
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

    def clean(self):
        cd = super().clean()
        if cd.get("password") and cd.get("confirm_password") and cd["password"] != cd["confirm_password"]:
            raise forms.ValidationError("Passwords do not match.")
        return cd


class CustomerRegistrationForm(BootstrapFormMixin,forms.Form):
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

    def clean(self):
        cd = super().clean()
        if cd.get("password") and cd.get("confirm_password") and cd["password"] != cd["confirm_password"]:
            raise forms.ValidationError("Passwords do not match.")
        return cd


class AdminRegistrationForm(BootstrapFormMixin,forms.Form):
    full_name = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=150)
    phone_no = forms.CharField(max_length=20)

    password = forms.CharField(widget=forms.PasswordInput(), validators=[validate_password_rules])
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        cd = super().clean()
        if cd.get("password") and cd.get("confirm_password") and cd["password"] != cd["confirm_password"]:
            raise forms.ValidationError("Passwords do not match.")
        return cd

 
class LoginForm(BootstrapFormMixin,forms.Form):
    email = forms.EmailField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput())
    remember_me = forms.BooleanField(required=False)