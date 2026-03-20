from decimal import Decimal
from django.utils import timezone

from applications.account_management.models import User, Business
from applications.order_management.models import Order, OrderLine, OrderBusiness, OrderStatus
from applications.inventory_management.models import Product


def status(name):
    return OrderStatus.objects.get_or_create(name=name)[0]


def make_order(customer, business_products, delivery_dt, final_status_name, suffix):
    order = Order(customer=customer, status=status("Pending"))
    order._updated_by = customer
    order.delivery_date = delivery_dt
    order.confirmed_price = Decimal("0.00")
    order.delivery_instructions = (
        f"Address: 110 Test Avenue, BS16 1GQ\n"
        f"Instructions: Demo seeded order {suffix}\n"
        f"PaymentRef: TEST-SEED-{suffix:04d}\n"
        f"PaymentStatus: SUCCESS (TEST MODE)"
    )
    order.save()

    total = Decimal("0.00")
    for business, product in business_products:
        OrderLine.objects.create(
            order=order,
            product=product,
            quantity=Decimal("1"),
            unit_price_at_order=product.price,
        )
        total += product.price

    order.confirmed_price = (total * Decimal("1.05")).quantize(Decimal("0.01"))
    order.save(update_fields=["confirmed_price"])

    for business, product in business_products:
        portion = OrderBusiness(order=order, business=business, status=status("Pending"), delivery_date=delivery_dt)
        portion._updated_by = customer
        portion._note_for_audit = "Seeded order created"
        portion.save()

        producer_user = business.contact_user

        if final_status_name in ["Confirmed", "Ready", "Delivered"]:
            portion.status = status("Confirmed")
            portion.note = "Seed: confirmed"
            portion._updated_by = producer_user
            portion._note_for_audit = portion.note
            portion.save(update_fields=["status", "note", "updated_at"])

        if final_status_name in ["Ready", "Delivered"]:
            portion.status = status("Ready")
            portion.note = "Seed: ready"
            portion._updated_by = producer_user
            portion._note_for_audit = portion.note
            portion.save(update_fields=["status", "note", "updated_at"])

        if final_status_name == "Delivered":
            portion.status = status("Delivered")
            portion.note = "Seed: delivered"
            portion._updated_by = producer_user
            portion._note_for_audit = portion.note
            portion.save(update_fields=["status", "note", "updated_at"])

    return order


customer = User.objects.filter(user_roles__role__name="Customer").order_by("id").first()
businesses = list(Business.objects.select_related("contact_user").order_by("id")[:2])

if not customer:
    raise Exception("Need at least one customer account before seeding orders.")
if len(businesses) < 2:
    raise Exception("Need at least two producer businesses before seeding orders.")

for name in ["Cart", "Pending", "Confirmed", "Ready", "Delivered", "Complete"]:
    status(name)

if Order.objects.exclude(status__name="Cart").count() >= 6:
    print("There are already 6 or more non-cart orders. Skipping seed.")
else:
    products_a = list(Product.objects.filter(business=businesses[0]).order_by("id")[:3])
    products_b = list(Product.objects.filter(business=businesses[1]).order_by("id")[:3])

    if len(products_a) < 3 or len(products_b) < 3:
        raise Exception("Need at least 3 products for each of the first 2 businesses.")

    now = timezone.now()

    # TC-021 için geçmiş delivered siparişler
    make_order(customer, [(businesses[0], products_a[0])], now - timezone.timedelta(days=14), "Delivered", 1)
    make_order(customer, [(businesses[1], products_b[0])], now - timezone.timedelta(days=10), "Delivered", 2)
    make_order(customer, [(businesses[0], products_a[1]), (businesses[1], products_b[1])], now - timezone.timedelta(days=7), "Delivered", 3)

    # TC-009 ve TC-010 için canlı producer siparişleri
    make_order(customer, [(businesses[0], products_a[2])], now + timezone.timedelta(days=3), "Pending", 4)
    make_order(customer, [(businesses[0], products_a[0]), (businesses[1], products_b[2])], now + timezone.timedelta(days=4), "Confirmed", 5)
    make_order(customer, [(businesses[1], products_b[1])], now + timezone.timedelta(days=5), "Ready", 6)

    print("Seeded demo order history and producer inbox orders.")

print("Non-cart orders:", Order.objects.exclude(status__name="Cart").count())