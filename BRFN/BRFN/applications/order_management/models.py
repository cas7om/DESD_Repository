from django.db import models
from applications.account_management.models import User
from applications.inventory_management.models import Product

class OrderStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name"], name="uq_orderstatus_name")
        ]

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

class Cart(models.Model):
    customer = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Cart(customer={self.customer_id})"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="uq_cart_product"
            )
        ]

    def __str__(self) -> str:
        return f"CartItem(cart={self.cart_id}, product={self.product_id}, qty={self.quantity})"