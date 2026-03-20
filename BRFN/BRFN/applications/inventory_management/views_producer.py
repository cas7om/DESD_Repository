from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect, get_object_or_404

from config.constants import SESSION_USER_ID_KEY
from config.decorators import login_required

from applications.account_management.models import Business
from .models import Product, StockItem, ProductCategory, Unit, ProduceAvailability

LOW_STOCK_THRESHOLD = Decimal("10")


def _get_business(request):
    user_id = request.session.get(SESSION_USER_ID_KEY)
    if not user_id:
        return None
    return Business.objects.filter(contact_user_id=user_id).first()


def _ensure_inventory_lookups():
    """Dropdown'lar boş kalmasın diye (dev amaçlı). İstersen sonra silebilirsin."""
    if not ProductCategory.objects.exists():
        ProductCategory.objects.get_or_create(name="General")
    if not Unit.objects.exists():
        Unit.objects.get_or_create(name="kg")
    if not ProduceAvailability.objects.exists():
        ProduceAvailability.objects.get_or_create(name="Available", defaults={"is_available": True})
        ProduceAvailability.objects.get_or_create(name="Unavailable", defaults={"is_available": False})


def _parse_decimal(value: str, field_name: str, places: int = 2) -> Decimal:
    raw = (value or "").strip()
    if raw == "":
        raise ValueError(f"{field_name} is required.")
    try:
        d = Decimal(raw)
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field_name} must be a number.")
    if d < 0:
        raise ValueError(f"{field_name} cannot be negative.")
    return d


@login_required
def producer_products(request):
    business = _get_business(request)

    if not business:
        messages.error(request, "No business is linked to this producer account.")
        return redirect("accounts:accounts_home")

    products = (
        Product.objects
        .filter(business=business)
        .select_related("business", "category", "unit", "availability", "stock")
        .order_by("-id")
    )

    # low-stock flag (StockItem yoksa crash olmasın)
    for p in products:
        try:
            qty = p.stock.quantity
        except StockItem.DoesNotExist:
            qty = None
        p.is_low_stock = bool(qty is not None and qty <= LOW_STOCK_THRESHOLD)

    total_products = products.count()
    available_count = products.filter(availability__is_available=True).count()
    unavailable_count = products.filter(availability__is_available=False).count()
    low_stock_count = sum(1 for p in products if getattr(p, "is_low_stock", False))

    # DİKKAT: template klasörün "Producer" (büyük P)
    return render(request, "Producer/products.html", {
        "products": products,
        "total_products": total_products,
        "available_count": available_count,
        "unavailable_count": unavailable_count,
        "low_stock_count": low_stock_count,
        "low_stock_threshold": LOW_STOCK_THRESHOLD,
    })


# --------------------------
# Producer: Add / Edit Product (ARTIK ÇALIŞIYOR)
# --------------------------

@login_required
def producer_product_new(request):
    business = _get_business(request)
    if not business:
        messages.error(request, "No business is linked to this producer account.")
        return redirect("accounts:accounts_home")

    _ensure_inventory_lookups()

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        category_id = request.POST.get("category")
        unit_id = request.POST.get("unit")
        availability_id = request.POST.get("availability")
        price_raw = request.POST.get("price")
        stock_raw = request.POST.get("stock")

        errors = []
        if not name:
            errors.append("Name is required.")

        try:
            price = _parse_decimal(price_raw, "Price", places=2)
        except ValueError as e:
            errors.append(str(e))
            price = None

        try:
            stock_qty = _parse_decimal(stock_raw, "Stock quantity", places=3)
        except ValueError as e:
            errors.append(str(e))
            stock_qty = None

        # FK doğrula
        category = ProductCategory.objects.filter(pk=category_id).first()
        unit = Unit.objects.filter(pk=unit_id).first()
        availability = ProduceAvailability.objects.filter(pk=availability_id).first()
        if not category:
            errors.append("Category is required.")
        if not unit:
            errors.append("Unit is required.")
        if not availability:
            errors.append("Availability is required.")

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            try:
                with transaction.atomic():
                    product = Product.objects.create(
                        business=business,
                        name=name,
                        price=price,
                        category=category,
                        unit=unit,
                        availability=availability,
                    )
                    StockItem.objects.update_or_create(
                        product=product,
                        defaults={"quantity": stock_qty},
                    )
                messages.success(request, "Product created successfully.")
                return redirect("inventory:producer_products")
            except IntegrityError:
                messages.error(request, "This product name already exists for your business.")

    return render(request, "Producer/product_form.html", {
        "mode": "create",
        "categories": ProductCategory.objects.order_by("name"),
        "units": Unit.objects.order_by("name"),
        "availabilities": ProduceAvailability.objects.order_by("name"),
        "low_stock_threshold": LOW_STOCK_THRESHOLD,
    })


@login_required
def producer_product_edit(request, pk: int):
    business = _get_business(request)
    if not business:
        messages.error(request, "No business is linked to this producer account.")
        return redirect("accounts:accounts_home")

    _ensure_inventory_lookups()

    product = get_object_or_404(
        Product.objects.select_related("category", "unit", "availability", "stock"),
        pk=pk,
        business=business,
    )

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        category_id = request.POST.get("category")
        unit_id = request.POST.get("unit")
        availability_id = request.POST.get("availability")
        price_raw = request.POST.get("price")
        stock_raw = request.POST.get("stock")

        errors = []
        if not name:
            errors.append("Name is required.")

        try:
            price = _parse_decimal(price_raw, "Price", places=2)
        except ValueError as e:
            errors.append(str(e))
            price = None

        try:
            stock_qty = _parse_decimal(stock_raw, "Stock quantity", places=3)
        except ValueError as e:
            errors.append(str(e))
            stock_qty = None

        category = ProductCategory.objects.filter(pk=category_id).first()
        unit = Unit.objects.filter(pk=unit_id).first()
        availability = ProduceAvailability.objects.filter(pk=availability_id).first()
        if not category:
            errors.append("Category is required.")
        if not unit:
            errors.append("Unit is required.")
        if not availability:
            errors.append("Availability is required.")

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            try:
                with transaction.atomic():
                    product.name = name
                    product.price = price
                    product.category = category
                    product.unit = unit
                    product.availability = availability
                    product.save()

                    StockItem.objects.update_or_create(
                        product=product,
                        defaults={"quantity": stock_qty},
                    )

                messages.success(request, "Product updated successfully.")
                return redirect("inventory:producer_products")
            except IntegrityError:
                messages.error(request, "This product name already exists for your business.")

    return render(request, "Producer/product_form.html", {
        "mode": "edit",
        "product": product,
        "categories": ProductCategory.objects.order_by("name"),
        "units": Unit.objects.order_by("name"),
        "availabilities": ProduceAvailability.objects.order_by("name"),
        "low_stock_threshold": LOW_STOCK_THRESHOLD,
    })


# --------------------------
# Producer: Alerts / Orders
# --------------------------

@login_required
def producer_alerts(request):
    business = _get_business(request)
    if not business:
        messages.error(request, "No business is linked to this producer account.")
        return redirect("accounts:accounts_home")

    low_stock_products = (
        Product.objects
        .filter(business=business, stock__quantity__lte=LOW_STOCK_THRESHOLD)
        .select_related("category", "unit", "availability", "stock")
        .order_by("name")
    )

    return render(request, "Producer/alerts.html", {
        "products": low_stock_products,
        "low_stock_threshold": LOW_STOCK_THRESHOLD,
    })


@login_required
def producer_orders(request):
    return redirect("orders:producer_inbox")