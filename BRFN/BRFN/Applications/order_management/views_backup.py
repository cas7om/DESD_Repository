from uuid import uuid4
from collections import defaultdict
from django.utils import timezone
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Sum, F

from config.constants import SESSION_USER_ID_KEY
from config.decorators import login_required, roles_required
from config.helpers import current_user_light, current_user, get_week_start_end

from applications.account_management.models import User, Business
from applications.inventory_management.models import Product, StockItem
from .models import Order, OrderAudit, OrderBusiness, OrderBusinessAudit, OrderLine, OrderStatus


def _current_user(request) -> User:
    user_id = request.session.get(SESSION_USER_ID_KEY)
    return User.objects.get(id=user_id)


def _get_or_create_cart_order(user: User) -> Order:
    cart_status, _ = OrderStatus.objects.get_or_create(name="Cart")

    cart = Order.objects.filter(customer=user, status=cart_status).first()
    if cart:
        return cart

    # order_ref max_length=10, keep it <= 10 chars
    order_ref = f"C{user.id:09d}"[-10:]
    return Order.objects.create(
        order_ref=order_ref,
        customer=user,
        status=cart_status,
    )


def _parse_qty(request) -> Decimal:
    raw = request.POST.get("quantity") or request.POST.get("qty") or request.POST.get("amount") or "1"
    try:
        return Decimal(str(raw))
    except (InvalidOperation, TypeError):
        return Decimal("0")

    STATUS_FLOW = ["Pending", "Confirmed", "Ready", "Delivered"]
STATUS_INDEX = {name: idx for idx, name in enumerate(STATUS_FLOW)}
ALLOWED_TRANSITIONS = {
    "Pending": {"Confirmed"},
    "Confirmed": {"Ready"},
    "Ready": {"Delivered"},
    "Delivered": set(),
}


def _get_status(name: str) -> OrderStatus:
    return OrderStatus.objects.get_or_create(name=name)[0]


def _group_lines_by_business(lines_qs):
    grouped = defaultdict(list)
    for ln in lines_qs:
        grouped[ln.product.business].append(ln)
    return grouped


def _overall_status_label(order: Order) -> str:
    portions = list(order.producer_orders.select_related("status", "business"))
    if not portions:
        return order.status.name

    unique_names = {portion.status.name for portion in portions}
    if len(unique_names) == 1:
        return portions[0].status.name
    return "Mixed"


def _payment_summary(order: Order):
    parsed = {
        "address": "",
        "instructions": "",
        "payment_ref": "",
        "payment_status": "",
    }
    for raw_line in (order.delivery_instructions or "").splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key == "address":
            parsed["address"] = value
        elif key == "instructions":
            parsed["instructions"] = value
        elif key == "paymentref":
            parsed["payment_ref"] = value
        elif key == "paymentstatus":
            parsed["payment_status"] = value

    ref = parsed["payment_ref"]
    if ref:
        parsed["payment_ref_masked"] = ("*" * max(0, len(ref) - 4)) + ref[-4:]
    else:
        parsed["payment_ref_masked"] = ""

    return parsed

@login_required
def cart_view(request):
    user = _current_user(request)
    cart_order = _get_or_create_cart_order(user)

    lines = (
        OrderLine.objects
        .filter(order=cart_order)
        .select_related("product")
        .order_by("product__name")
    )

    subtotal = Decimal("0.00")
    display_lines = []

    for ln in lines:
        line_total = (ln.unit_price_at_order * ln.quantity)
        subtotal += line_total
        display_lines.append({
            "product": ln.product,
            "quantity": ln.quantity,
            "unit_price": ln.unit_price_at_order,
            "line_total": line_total,
        })

    return render(request, "order_management/cart.html", {
        "lines": display_lines,
        "subtotal": subtotal,
    })


@login_required
def cart_add(request, product_id: int):
    if request.method != "POST":
        return redirect("orders:cart")

    user = _current_user(request)
    cart_order = _get_or_create_cart_order(user)
    product = get_object_or_404(Product, id=product_id)

    qty = _parse_qty(request)
    if qty <= 0:
        messages.error(request, "Quantity must be greater than 0.")
        return redirect("orders:cart")

    # Replace quantity if already exists (matches TC-006)
    line = OrderLine.objects.filter(order=cart_order, product=product).first()
    if line:
        line.quantity = qty
        line.unit_price_at_order = product.price
        line.save(update_fields=["quantity", "unit_price_at_order"])
    else:
        OrderLine.objects.create(
            order=cart_order,
            product=product,
            quantity=qty,
            unit_price_at_order=product.price,
        )

    messages.success(request, "Item added to cart.")
    return redirect("orders:cart")


@login_required
def cart_update(request):
    if request.method != "POST":
        return redirect("orders:cart")

    user = _current_user(request)
    cart_order = _get_or_create_cart_order(user)

    # Expect inputs like qty_<product_id>
    updated_any = False

    for key, value in request.POST.items():
        if not key.startswith("qty_"):
            continue

        try:
            pid = int(key.replace("qty_", ""))
        except ValueError:
            continue

        try:
            qty = Decimal(str(value))
        except (InvalidOperation, TypeError):
            qty = Decimal("0")

        line = OrderLine.objects.filter(order=cart_order, product_id=pid).first()
        if not line:
            continue

        if qty <= 0:
            line.delete()
            updated_any = True
        else:
            line.quantity = qty
            line.save(update_fields=["quantity"])
            updated_any = True

    if updated_any:
        messages.success(request, "Cart updated.")

    return redirect("orders:cart")


@login_required
def cart_remove(request, product_id: int):
    user = _current_user(request)
    cart_order = _get_or_create_cart_order(user)

    OrderLine.objects.filter(order=cart_order, product_id=product_id).delete()
    messages.success(request, "Item removed from cart.")
    return redirect("orders:cart")

@login_required
def checkout_view(request):
    user = _current_user(request)
    cart_order = _get_or_create_cart_order(user)

    lines_qs = (
        OrderLine.objects
        .filter(order=cart_order)
        .select_related("product", "product__business")
    )

    if not lines_qs.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("orders:cart")

    # single producer rule
    business_ids = {ln.product.business_id for ln in lines_qs}
    if len(business_ids) != 1:
        messages.error(request, "Checkout is only available for a single producer. Please adjust your cart.")
        return redirect("orders:cart")

    producer = lines_qs.first().product.business

    subtotal = Decimal("0.00")
    items = []
    for ln in lines_qs:
        line_total = ln.unit_price_at_order * ln.quantity
        subtotal += line_total
        items.append({
            "product": ln.product,
            "quantity": ln.quantity,
            "unit_price": ln.unit_price_at_order,
            "line_total": line_total,
        })

    commission = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
    total = (subtotal + commission).quantize(Decimal("0.01"))

    min_delivery_dt = timezone.now() + timezone.timedelta(hours=48)

    if request.method == "GET":
        return render(request, "order_management/checkout.html", {
            "producer": producer,
            "items": items,
            "subtotal": subtotal.quantize(Decimal("0.01")),
            "commission": commission,
            "total": total,
            "min_delivery_dt": min_delivery_dt,
        })

    # POST
    delivery_date_raw = request.POST.get("delivery_date", "")
    delivery_address = request.POST.get("delivery_address", "").strip()
    delivery_instructions = request.POST.get("delivery_instructions", "").strip()

    if not delivery_address:
        messages.error(request, "Delivery address is required.")
        return redirect("orders:checkout")

    try:
        naive = timezone.datetime.fromisoformat(delivery_date_raw)
        delivery_dt = timezone.make_aware(naive, timezone.get_current_timezone())
    except Exception:
        messages.error(request, "Please select a valid delivery date/time.")
        return redirect("orders:checkout")

    if delivery_dt < min_delivery_dt:
        messages.error(request, "Delivery date must be at least 48 hours from now.")
        return redirect("orders:checkout")

        pending_status, _ = OrderStatus.objects.get_or_create(name="Pending")

    payment_ref = f"TEST-{uuid4().hex[:12]}"

    cart_order.status = pending_status

    # "record payment" inside delivery_instructions (test mode)
    payment_ref = f"TEST-{uuid4().hex[:12]}"

    cart_order.status = pending_status
    cart_order.confirmed_price = total
    cart_order.delivery_date = delivery_dt
    cart_order.delivery_instructions = (
        f"Address: {delivery_address}\n"
        f"Instructions: {delivery_instructions}\n"
        f"PaymentRef: {payment_ref}\n"
        f"PaymentStatus: SUCCESS (TEST MODE)"
    ).strip()
    cart_order.save(update_fields=["status", "confirmed_price", "delivery_date", "delivery_instructions"])

    return redirect("orders:confirmation", order_ref=cart_order.order_ref)


@login_required
def order_confirmation(request, order_ref: str):
    user = _current_user(request)
    order = get_object_or_404(Order, order_ref=order_ref, customer=user)

    lines_qs = OrderLine.objects.filter(order=order).select_related("product", "product__business")

    subtotal = Decimal("0.00")
    items = []
    producer = None
    for ln in lines_qs:
        producer = producer or ln.product.business
        line_total = ln.unit_price_at_order * ln.quantity
        subtotal += line_total
        items.append({
            "product": ln.product,
            "quantity": ln.quantity,
            "unit_price": ln.unit_price_at_order,
            "line_total": line_total,
        })

    commission = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
    total = (subtotal + commission).quantize(Decimal("0.01"))

    return render(request, "order_management/confirmation.html", {
        "order": order,
        "producer": producer,
        "items": items,
        "subtotal": subtotal.quantize(Decimal("0.01")),
        "commission": commission,
        "total": total,
    })