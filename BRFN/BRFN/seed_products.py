from django.contrib.auth.hashers import make_password
from applications.account_management.models import (
    Business, User, Role, UserRole, Address, UserAddress
)
from applications.inventory_management.models import (
    ProductCategory,
    Unit,
    ProduceAvailability,
    Product,
    StockItem,
)

#Producer 1
contact_user, _ = User.objects.get_or_create(
    email="pproducer@test.com",
    defaults={
        "full_name": "Peter Producer",
        "phone_no": "0123456789",
        "password_hash": make_password("Hello1234!"),
    },
)

producer_role, _ = Role.objects.get_or_create(name="Producer")
UserRole.objects.get_or_create(user=contact_user, role=producer_role)

business_addr, _ = Address.objects.get_or_create(
    line1="1 Test Close",
    line2="Test Town",
    line3="",
    postcode="BS1 1AA",
)

UserAddress.objects.get_or_create(user=contact_user, address=business_addr)

Business.objects.get_or_create(
    business_name="Peter's Produce",
    defaults={
        "address": business_addr,
        "contact_user": contact_user,
    },
)

#Producer 2
contact_user, _ = User.objects.get_or_create(
    email="farmer_tim@test.com",
    defaults={
        "full_name": "Tim Farmer",
        "phone_no": "0987654321",
        "password_hash": make_password("Hello1234!"),
    },
)

UserRole.objects.get_or_create(user=contact_user, role=producer_role)

business_addr, _ = Address.objects.get_or_create(
    line1="110 Test Lane",
    line2="Test Town",
    line3="",
    postcode="BS2 1AB",
)

UserAddress.objects.get_or_create(user=contact_user, address=business_addr)

Business.objects.get_or_create(
    business_name="Tim's Tomatoes",
    defaults={
        "address": business_addr,
        "contact_user": contact_user,
    },
)

veg, _ = ProductCategory.objects.get_or_create(name="Vegetables")
fruit, _ = ProductCategory.objects.get_or_create(name="Fruits")
dairy, _ = ProductCategory.objects.get_or_create(name="Dairy")

kg, _ = Unit.objects.get_or_create(name="kg")
pack, _ = Unit.objects.get_or_create(name="pack")
litre, _ = Unit.objects.get_or_create(name="litre")
bunch, _ = Unit.objects.get_or_create(name="bunch")

available, _ = ProduceAvailability.objects.get_or_create(
    name="Available",
    defaults={"is_available": True},
)
if not available.is_available:
    available.is_available = True
    available.save()

unavailable, _ = ProduceAvailability.objects.get_or_create(
    name="Unavailable",
    defaults={"is_available": False},
)
if unavailable.is_available:
    unavailable.is_available = False
    unavailable.save()

business1 = Business.objects.filter(business_name="Peter's Produce").first()
business2 = Business.objects.filter(business_name="Tim's Tomatoes").first()

if not business1 or not business2:
    raise Exception("Both producer businesses must exist first. Create the 2 producer accounts from the website before running this script.")

products_by_business = {
    business1: [
        ("Carrots", veg, kg, available, "2.50", "35"),
        ("Potatoes", veg, kg, available, "1.80", "60"),
        ("Broccoli", veg, bunch, available, "1.40", "22"),
        ("Spinach", veg, pack, available, "1.95", "18"),

        ("Apples", fruit, kg, available, "3.20", "40"),
        ("Strawberries", fruit, pack, available, "2.90", "25"),
        ("Bananas", fruit, kg, available, "2.10", "30"),
        ("Pears", fruit, kg, available, "3.00", "15"),

        ("Whole Milk", dairy, litre, available, "1.60", "50"),
        ("Cheddar Cheese", dairy, pack, available, "3.75", "20"),
        ("Greek Yogurt", dairy, pack, available, "2.30", "16"),
        ("Salted Butter", dairy, pack, available, "2.80", "14"),
    ],
    business2: [
        ("Tomatoes", veg, kg, available, "2.70", "33"),
        ("Cucumbers", veg, kg, available, "2.00", "21"),
        ("Lettuce", veg, bunch, available, "1.20", "19"),
        ("Peppers", veg, pack, available, "2.45", "17"),

        ("Oranges", fruit, kg, available, "3.10", "28"),
        ("Grapes", fruit, pack, available, "2.85", "24"),
        ("Blueberries", fruit, pack, available, "3.95", "12"),
        ("Mangoes", fruit, kg, available, "4.20", "10"),

        ("Semi-Skimmed Milk", dairy, litre, available, "1.55", "38"),
        ("Mozzarella", dairy, pack, available, "2.95", "18"),
        ("Natural Yogurt", dairy, pack, available, "2.10", "20"),
        ("Unsalted Butter", dairy, pack, available, "2.75", "13"),
    ],
}

for business, items in products_by_business.items():
    for name, category, unit, availability, price, qty in items:
        product, _ = Product.objects.get_or_create(
            business=business,
            name=name,
            defaults={
                "category": category,
                "unit": unit,
                "availability": availability,
                "price": price,
            },
        )

        product.category = category
        product.unit = unit
        product.availability = availability
        product.price = price
        product.save()

        StockItem.objects.update_or_create(
            product=product,
            defaults={"quantity": qty},
        )

print("Done.")
print("Categories:", ProductCategory.objects.count())
print("Total products:", Product.objects.count())
print("Business 1 products:", Product.objects.filter(business=business1).count())
print("Business 2 products:", Product.objects.filter(business=business2).count())