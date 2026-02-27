from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from config.decorators import admin_required

from .models import Allergen

from .forms import SaveAllergenForm


def inventory_home(request):
    return render(request, "inventory.html")

@admin_required 
def allergen_list(request):
    allergens = (
        Allergen.objects.all()
    )
    return render(request, "allergens/list_allergen.html", {"allergens": allergens})

@admin_required
@transaction.atomic
def allergen_save(request, pk=None):
    allergen = None
    if pk:
        allergen = get_object_or_404(Allergen, pk=pk)

    if request.method == "POST":
        form = SaveAllergenForm(request.POST, instance=allergen)
        if form.is_valid():
            form.save()
            messages.success(request, "Allergen saved successfully.")
            return redirect("inventory:inventory_home")
    else:
        form = SaveAllergenForm(instance=allergen)

    action = "Update" if allergen else "Create"
    return render(request, "allergens/save_allergen.html", {
        "form": form,
        "action": action,
        "allergen": allergen,
    })
