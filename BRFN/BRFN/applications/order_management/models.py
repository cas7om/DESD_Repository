import random
import string

from django.db import models
from applications.account_management.models import User, Business
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

    def generate_order_ref(self):
        letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        numbers = ''.join(random.choices(string.digits, k=3))
        return letters + numbers

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None

        if not is_new:
            old_status = Order.objects.get(pk=self.pk).status

        if is_new:
            ref = self.generate_order_ref()
            while Order.objects.filter(order_ref=ref).exists():
                ref = self.generate_order_ref()
            self.order_ref = ref

            super().save(*args, **kwargs)

            OrderAudit.objects.create(
                order=self,
                from_status=None,
                to_status=self.status,
                updated_by=self._updated_by,
            )
        elif old_status != self.status:
            super().save(*args, **kwargs)
            OrderAudit.objects.create(
                order=self,
                from_status=old_status,
                to_status=self.status,
                updated_by=self._updated_by,
            )
        else:
            super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.order_ref


class OrderAudit(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="audits")
    from_status = models.ForeignKey(
        OrderStatus,
        on_delete=models.PROTECT,
        related_name="audits_from",
        null=True,
        default=None,
    )
    to_status = models.ForeignKey(
        OrderStatus,
        on_delete=models.PROTECT,
        related_name="audits_to",
    )
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    updated_on = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.order.order_ref} was changed from {self.from_status.name if self.from_status else None} to {self.to_status.name} on {self.updated_on} by {self.updated_by.email}"


class OrderBusiness(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="producer_orders")
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="producer_orders")
    status = models.ForeignKey(OrderStatus, on_delete=models.PROTECT)
    delivery_date = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["order", "business"], name="uq_order_business")
        ]

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None

        if not is_new:
            old_status = OrderBusiness.objects.get(pk=self.pk).status

        super().save(*args, **kwargs)

        if is_new:
            OrderBusinessAudit.objects.create(
                producer_order=self,
                from_status=None,
                to_status=self.status,
                updated_by=self._updated_by,
                note=getattr(self, "_note_for_audit", ""),
            )
        elif old_status != self.status:
            OrderBusinessAudit.objects.create(
                producer_order=self,
                from_status=old_status,
                to_status=self.status,
                updated_by=self._updated_by,
                note=getattr(self, "_note_for_audit", ""),
            )

    def __str__(self):
        return f"{self.order.order_ref} / {self.business.business_name}"


class OrderBusinessAudit(models.Model):
    producer_order = models.ForeignKey(OrderBusiness, on_delete=models.CASCADE, related_name="audits")
    from_status = models.ForeignKey(
        OrderStatus,
        on_delete=models.PROTECT,
        related_name="producer_audits_from",
        null=True,
        default=None,
    )
    to_status = models.ForeignKey(
        OrderStatus,
        on_delete=models.PROTECT,
        related_name="producer_audits_to",
    )
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.CharField(max_length=300, blank=True)
    updated_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.producer_order} {self.from_status} -> {self.to_status}"


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

