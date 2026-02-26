from django.db import models
from applications.account_management.models import Business

class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name"], name="uq_prodcat_name")
        ]

    def __str__(self) -> str:
        return self.name


class Unit(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name"], name="uq_unit_name")
        ]


    def __str__(self) -> str:
        return self.name


class ProduceAvailability(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_available = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name"], name="uq_prodavail_name")
        ]

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

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name"], name="uq_allergen_name")
        ]

    def __str__(self) -> str:
        return self.name


class ProductAllergen(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    allergen = models.ForeignKey(Allergen, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "allergen"], name="uq_product_allergen")
        ]
