from django import forms
from config.forms import BootstrapFormMixin
from .models import Allergen

class SaveAllergenForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Allergen
        fields = ["name"]

    name = forms.CharField(max_length=50)