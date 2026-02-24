from django.db import models

class User(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=150, unique=True)
    phone_no = models.CharField(max_length=20, blank=True)
    password_hash = models.CharField(max_length=300)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email})"


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="role_users")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], name="uq_user_role")
        ]

    def __str__(self) -> str:
        return f"{self.user_id} -> {self.role.name}"


class Address(models.Model):
    line1 = models.CharField(max_length=80)
    line2 = models.CharField(max_length=80, blank=True)
    line3 = models.CharField(max_length=80, blank=True)
    postcode = models.CharField(max_length=10)

    def __str__(self) -> str:
        return f"{self.line1}, {self.postcode}"


class UserAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    address = models.ForeignKey(Address, on_delete=models.PROTECT)

    def __str__(self) -> str:
        return f"{self.user_id} [{self.address_type.name}] -> {self.address_id}"


class Business(models.Model):
    business_name = models.CharField(max_length=100, unique=True)
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="businesses")
    contact_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="managed_businesses")

    def __str__(self) -> str:
        return self.business_name


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class Unit(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class ProduceAvailability(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_available = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    availability = models.ForeignKey(ProduceAvailability, on_delete=models.PROTECT)

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["business", "name"], name="uq_business_productname")
        ]

    def __str__(self) -> str:
        return self.name


class StockItem(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="stock")
    quantity = models.DecimalField(max_digits=12, decimal_places=3)

    def __str__(self) -> str:
        return f"{self.product_id} qty={self.quantity}"


class Allergen(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class ProductAllergen(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    allergen = models.ForeignKey(Allergen, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "allergen"], name="uq_product_allergen")
        ]


class OrderStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    order_ref = models.CharField(max_length=10, unique=True)
    customer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    status = models.ForeignKey(OrderStatus, on_delete=models.PROTECT)

    confirmed_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    delivery_instructions = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.order_ref


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)

    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price_at_order = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["order", "product"], name="uq_order_product")
        ]

    def __str__(self) -> str:
        return f"OrderLine(order={self.order_id}, product={self.product_id}, qty={self.quantity})"