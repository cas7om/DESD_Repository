from django import forms
from config.forms import BootstrapFormMixin

class CreateAllergenForm(BootstrapFormMixin,forms.Form):
    name = forms.CharField(max_length=50)