from uuid import uuid4
from collections import defaultdict
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from config.decorators import login_required, roles_required
from config.helpers import current_user_light, get_week_start_end

from applications.account_management.models import User, Business
from applications.inventory_management.models import Product
from .models import Order, OrderBusiness, OrderLine, OrderStatus


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


def _ensure_order_statuses():
    for name in ["Cart", "Pending", "Confirmed", "Ready", "Delivered", "Complete"]:
        _get_status(name)


def _get_or_create_cart_order(user: User) -> Order:
    cart_status = _get_status("Cart")
    cart = Order.objects.filter(customer=user, status=cart_status).first()
    if cart:
        return cart

    order = Order(customer=user, status=cart_status)
    order._updated_by = user
    order.save()
    return order


def _parse_qty(request) -> Decimal:
    raw = request.POST.get("quantity") or request.POST.get("qty") or request.POST.get("amount") or "1"
    try:
        return Decimal(str(raw))
    except (InvalidOperation, TypeError):
        return Decimal("0")


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


def _safe_food_miles(product, user):
    try:
        if not user or not getattr(user, "addresses", None):
            return 0
        if not user.addresses.exists():
            return 0

        postcode = user.addresses.first().address.postcode
        calc_fn = getattr(product, "calculate_distance", None)

        if callable(calc_fn):
            return calc_fn(postcode) or 0

        return 0
    except Exception:
        return 0


@login_required
def cart_view(request):
    user = current_user_light(request)
    cart_order = _get_or_create_cart_order(user)

    lines = (
        OrderLine.objects
        .filter(order=cart_order)
        .select_related("product", "product__business")
        .order_by("product__business__business_name", "product__name")
    )

    subtotal = Decimal("0.00")
    order_food_miles = 0
    display_lines = []

    for ln in lines:
        line_total = ln.unit_price_at_order * ln.quantity
        subtotal += line_total

        ln_food_miles = _safe_food_miles(ln.product, user)
        order_food_miles += ln_food_miles

        display_lines.append({
            "product": ln.product,
            "quantity": ln.quantity,
            "unit_price": ln.unit_price_at_order,
            "line_total": line_total,
            "line_food_miles": ln_food_miles,
            "business_name": ln.product.business.business_name,
        })

    grouped_lines = defaultdict(list)
    for line in display_lines:
        grouped_lines[line["business_name"]].append(line)

    return render(request, "order_management/cart.html", {
        "lines": display_lines,
        "grouped_lines": dict(grouped_lines),
        "subtotal": subtotal.quantize(Decimal("0.01")),
        "order_food_miles": order_food_miles,
    })


@login_required
def cart_add(request, product_id: int):
    if request.method != "POST":
        return redirect("orders:cart")

    user = current_user_light(request)
    cart_order = _get_or_create_cart_order(user)
    product = get_object_or_404(
        Product.objects.select_related("availability", "stock", "business"),
        id=product_id,
    )

    qty = _parse_qty(request)
    if qty <= 0:
        messages.error(request, "Quantity must be greater than 0.")
        return redirect("orders:cart")

    availability = getattr(product, "availability", None)
    if availability and not availability.is_available:
        messages.error(request, f"{product.name} is currently unavailable.")
        return redirect("orders:cart")

    stock_qty = getattr(getattr(product, "stock", None), "quantity", Decimal("0"))
    if stock_qty <= 0:
        messages.error(request, f"{product.name} is out of stock.")
        return redirect("orders:cart")

    if qty > stock_qty:
        messages.warning(request, f"Only {stock_qty} available for {product.name}. Quantity adjusted.")
        qty = stock_qty

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

    user = current_user_light(request)
    cart_order = _get_or_create_cart_order(user)

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

        line = OrderLine.objects.filter(order=cart_order, product_id=pid).select_related("product__stock").first()
        if not line:
            continue

        if qty <= 0:
            line.delete()
            updated_any = True
            continue

        stock_qty = getattr(getattr(line.product, "stock", None), "quantity", qty)
        if qty > stock_qty:
            messages.warning(request, f"Only {stock_qty} available for {line.product.name}. Quantity adjusted.")
            qty = stock_qty

        line.quantity = qty
        line.save(update_fields=["quantity"])
        updated_any = True

    if updated_any:
        messages.success(request, "Cart updated.")

    return redirect("orders:cart")


@login_required
def cart_remove(request, product_id: int):
    user = current_user_light(request)
    cart_order = _get_or_create_cart_order(user)
    OrderLine.objects.filter(order=cart_order, product_id=product_id).delete()
    messages.success(request, "Item removed from cart.")
    return redirect("orders:cart")


@login_required
def checkout_view(request):
    _ensure_order_statuses()
    user = current_user_light(request)
    cart_order = _get_or_create_cart_order(user)

    lines_qs = (
        OrderLine.objects
        .filter(order=cart_order)
        .select_related("product", "product__business", "product__unit", "product__stock")
    )

    if not lines_qs.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("orders:cart")

    grouped = _group_lines_by_business(lines_qs)
    subtotal = Decimal("0.00")
    order_food_miles = 0
    sections = []

    for business, lines in grouped.items():
        section_total = Decimal("0.00")
        section_items = []

        for ln in lines:
            line_total = ln.unit_price_at_order * ln.quantity
            section_total += line_total
            subtotal += line_total

            maybe_miles = _safe_food_miles(ln.product, user)
            order_food_miles += maybe_miles

            section_items.append({
                "product": ln.product,
                "quantity": ln.quantity,
                "unit_price": ln.unit_price_at_order,
                "line_total": line_total,
                "line_food_miles": maybe_miles,
            })

        sections.append({
            "business": business,
            "items": section_items,
            "subtotal": section_total.quantize(Decimal("0.01")),
        })

    commission = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
    total = (subtotal + commission).quantize(Decimal("0.01"))
    min_delivery_dt = timezone.now() + timezone.timedelta(hours=48)

    default_address = ""
    if getattr(user, "addresses", None) and user.addresses.exists():
        addr = user.addresses.first().address
        default_address = ", ".join([v for v in [addr.line1, addr.line2, addr.line3, addr.postcode] if v])

    if request.method == "GET":
        return render(request, "order_management/checkout.html", {
            "producer_sections": sections,
            "subtotal": subtotal.quantize(Decimal("0.01")),
            "commission": commission,
            "total": total,
            "min_delivery_dt": min_delivery_dt,
            "order_food_miles": order_food_miles,
            "default_address": default_address,
        })

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

    pending_status = _get_status("Pending")
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
    cart_order._updated_by = user
    cart_order.save(update_fields=["status", "confirmed_price", "delivery_date", "delivery_instructions"])

    for business, _business_lines in grouped.items():
        portion = OrderBusiness.objects.filter(order=cart_order, business=business).first()
        if portion is None:
            portion = OrderBusiness(
                order=cart_order,
                business=business,
                status=pending_status,
                delivery_date=delivery_dt,
            )
            portion._updated_by = user
            portion._note_for_audit = "Order created during checkout"
            portion.save()

    messages.success(request, "Order placed successfully in test mode.")
    return redirect("orders:confirmation", order_ref=cart_order.order_ref)


@login_required
def order_confirmation(request, order_ref: str):
    user = current_user_light(request)
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


@login_required
@roles_required("Admin", "Producer")
def settlements(request):
    week_start, week_end = get_week_start_end()
    current = current_user_light(request)

    if current.has_role("Admin"):
        businesses = Business.objects.all()
    elif current.has_role("Producer"):
        businesses = Business.objects.filter(contact_user=current)
    else:
        messages.error(request, "Access Denied.")
        return redirect("inventory:inventory_home")

    week_completed_orders = Order.objects.filter(
        producer_orders__status__name="Delivered",
        producer_orders__updated_at__date__gte=week_start,
        producer_orders__updated_at__date__lt=week_end,
    ).distinct()

    lines = (
        OrderLine.objects
        .filter(order__in=week_completed_orders, product__business__in=businesses)
        .select_related("order", "product", "product__unit", "product__business")
        .annotate(line_total=F("quantity") * F("unit_price_at_order"))
    )

    result = {}
    for line in lines:
        business = line.product.business
        order = line.order

        if business.id not in result:
            result[business.id] = {"business": business, "orders": {}}

        if order.id not in result[business.id]["orders"]:
            result[business.id]["orders"][order.id] = {
                "order": order,
                "order_ref": order.order_ref,
                "lines": [],
            }

        result[business.id]["orders"][order.id]["lines"].append({
            "orderline": line,
            "product_name": line.product.name,
            "product_unit": line.product.unit.name,
            "quantity": line.quantity,
            "unit_price": line.unit_price_at_order,
            "line_total": line.line_total,
        })

    context = {
        "payouts": result,
        "start": week_start,
        "end": week_end,
    }
    return render(request, "order_management/settlements.html", context)


@login_required
@roles_required("Customer")
def customer_order_history(request):
    user = current_user_light(request)
    orders = (
        Order.objects
        .filter(customer=user)
        .exclude(status__name="Cart")
        .prefetch_related(
            "producer_orders__business",
            "producer_orders__status",
            "lines__product__business",
        )
        .order_by("-created_at")
    )

    producer_filter = (request.GET.get("producer") or "").strip()
    start_date = (request.GET.get("start") or "").strip()
    end_date = (request.GET.get("end") or "").strip()

    if producer_filter:
        orders = orders.filter(producer_orders__business__business_name__icontains=producer_filter).distinct()
    if start_date:
        orders = orders.filter(created_at__date__gte=start_date)
    if end_date:
        orders = orders.filter(created_at__date__lte=end_date)

    rows = []
    for order in orders:
        producer_names = sorted({portion.business.business_name for portion in order.producer_orders.all()})
        rows.append({
            "order": order,
            "producer_names": producer_names,
            "overall_status": _overall_status_label(order),
            "payment": _payment_summary(order),
        })

    return render(request, "order_management/customer_order_history.html", {
        "rows": rows,
        "producer_filter": producer_filter,
        "start_date": start_date,
        "end_date": end_date,
    })


@login_required
@roles_required("Customer")
def customer_order_detail(request, order_ref: str):
    user = current_user_light(request)
    order = get_object_or_404(
        Order.objects.prefetch_related(
            "producer_orders__business",
            "producer_orders__status",
            "producer_orders__audits__updated_by",
            "producer_orders__audits__from_status",
            "producer_orders__audits__to_status",
            "lines__product__business",
        ),
        order_ref=order_ref,
        customer=user,
    )

    grouped = _group_lines_by_business(order.lines.all())
    sections = []
    subtotal = Decimal("0.00")
    for business, lines in grouped.items():
        section_total = Decimal("0.00")
        items = []
        for ln in lines:
            line_total = ln.unit_price_at_order * ln.quantity
            subtotal += line_total
            section_total += line_total
            items.append({
                "product": ln.product,
                "quantity": ln.quantity,
                "unit_price": ln.unit_price_at_order,
                "line_total": line_total,
            })
        portion = order.producer_orders.filter(business=business).first()
        sections.append({
            "business": business,
            "status": portion.status.name if portion else order.status.name,
            "delivery_date": portion.delivery_date if portion and portion.delivery_date else order.delivery_date,
            "items": items,
            "subtotal": section_total.quantize(Decimal("0.01")),
            "audits": portion.audits.all().order_by("-updated_on") if portion else [],
        })

    commission = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
    total = (subtotal + commission).quantize(Decimal("0.01"))

    return render(request, "order_management/customer_order_detail.html", {
        "order": order,
        "producer_sections": sections,
        "subtotal": subtotal.quantize(Decimal("0.01")),
        "commission": commission,
        "total": total,
        "overall_status": _overall_status_label(order),
        "payment": _payment_summary(order),
    })


@login_required
@roles_required("Customer")
def reorder_order(request, order_ref: str):
    user = current_user_light(request)
    previous_order = get_object_or_404(Order, order_ref=order_ref, customer=user)
    cart_order = _get_or_create_cart_order(user)

    unavailable = []
    added = 0
    for previous_line in previous_order.lines.select_related("product", "product__availability", "product__stock"):
        product = previous_line.product

        availability = getattr(product, "availability", None)
        if availability and not availability.is_available:
            unavailable.append(f"{product.name} (unavailable)")
            continue

        stock_qty = getattr(getattr(product, "stock", None), "quantity", Decimal("0"))
        if stock_qty <= 0:
            unavailable.append(f"{product.name} (out of stock)")
            continue

        qty = previous_line.quantity if previous_line.quantity <= stock_qty else stock_qty
        line = OrderLine.objects.filter(order=cart_order, product=product).first()
        if line:
            new_qty = line.quantity + qty
            if new_qty > stock_qty:
                new_qty = stock_qty
            line.quantity = new_qty
            line.unit_price_at_order = product.price
            line.save(update_fields=["quantity", "unit_price_at_order"])
        else:
            OrderLine.objects.create(
                order=cart_order,
                product=product,
                quantity=qty,
                unit_price_at_order=product.price,
            )
        added += 1

    if added:
        messages.success(request, "Previous order items added to your cart.")
    if unavailable:
        messages.warning(request, "Some products could not be reordered: " + ", ".join(unavailable))

    return redirect("orders:cart")


@login_required
@roles_required("Producer")
def producer_order_inbox(request):
    producer_user = current_user_light(request)
    business = Business.objects.filter(contact_user=producer_user).first()
    if not business:
        messages.error(request, "No business is linked to this producer account.")
        return redirect("accounts:accounts_home")

    portions = (
        OrderBusiness.objects
        .filter(business=business)
        .select_related("order", "order__customer", "status")
        .prefetch_related("order__lines__product__business")
        .order_by("delivery_date", "-created_at")
    )

    status_filter = (request.GET.get("status") or "").strip()
    if status_filter:
        portions = portions.filter(status__name__iexact=status_filter)

    rows = []
    for portion in portions:
        relevant_lines = portion.order.lines.filter(product__business=business).select_related("product")
        subtotal = Decimal("0.00")
        item_count = 0
        for line in relevant_lines:
            subtotal += line.unit_price_at_order * line.quantity
            item_count += 1
        rows.append({
            "portion": portion,
            "customer": portion.order.customer,
            "item_count": item_count,
            "subtotal": subtotal.quantize(Decimal("0.01")),
            "payment": _payment_summary(portion.order),
        })

    return render(request, "order_management/producer_order_inbox.html", {
        "rows": rows,
        "status_filter": status_filter,
        "status_options": STATUS_FLOW,
        "business": business,
    })


@login_required
@roles_required("Producer")
def producer_order_detail(request, portion_id: int):
    producer_user = current_user_light(request)
    business = Business.objects.filter(contact_user=producer_user).first()
    portion = get_object_or_404(
        OrderBusiness.objects.select_related("order", "order__customer", "business", "status").prefetch_related(
            "order__lines__product__business",
            "audits__from_status",
            "audits__to_status",
            "audits__updated_by",
        ),
        id=portion_id,
        business=business,
    )

    relevant_lines = portion.order.lines.filter(product__business=business).select_related("product")
    subtotal = Decimal("0.00")
    items = []
    for line in relevant_lines:
        line_total = line.unit_price_at_order * line.quantity
        subtotal += line_total
        items.append({
            "product": line.product,
            "quantity": line.quantity,
            "unit_price": line.unit_price_at_order,
            "line_total": line_total,
        })

    next_statuses = sorted(ALLOWED_TRANSITIONS.get(portion.status.name, set()), key=lambda name: STATUS_INDEX[name])

    return render(request, "order_management/producer_order_detail.html", {
        "portion": portion,
        "items": items,
        "subtotal": subtotal.quantize(Decimal("0.01")),
        "payment": _payment_summary(portion.order),
        "next_statuses": next_statuses,
    })


@login_required
@roles_required("Producer")
def producer_order_update_status(request, portion_id: int):
    if request.method != "POST":
        return redirect("orders:producer_inbox")

    producer_user = current_user_light(request)
    business = Business.objects.filter(contact_user=producer_user).first()
    portion = get_object_or_404(OrderBusiness.objects.select_related("status", "order"), id=portion_id, business=business)

    new_status_name = (request.POST.get("status") or "").strip()
    note = (request.POST.get("note") or "").strip()

    allowed = ALLOWED_TRANSITIONS.get(portion.status.name, set())
    if new_status_name not in allowed:
        messages.error(request, f"Invalid status change. {portion.status.name} can only move to: {', '.join(sorted(allowed)) or 'no further status'}.")
        return redirect("orders:producer_order_detail", portion_id=portion.id)

    new_status = _get_status(new_status_name)
    portion.status = new_status
    portion.note = note
    portion._updated_by = producer_user
    portion._note_for_audit = note
    portion.save(update_fields=["status", "note", "updated_at"])

    messages.success(request, f"Order {portion.order.order_ref} updated to {new_status_name}.")
    return redirect("orders:producer_order_detail", portion_id=portion.id)