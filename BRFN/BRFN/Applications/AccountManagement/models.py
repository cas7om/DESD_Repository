from django.db import models
from django.core.validators import MinValueValidator, EmailValidator

class Address(models.Model):
    address = models.TextField()
    postcode = models.CharField(max_length=6)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return self.address

class UserRole(models.Model):
    user_role_name = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = "User Roles"
        constraints = [
            models.UniqueConstraint(fields=["user_role_name"], name="unique_role_name")
        ]

    def __str__(self):
        return self.user_role_name

class User(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    password = models.CharField(max_length=300)
    user_role = models.ForeignKey(UserRole)

    class Meta:
        verbose_name_plural = "Users"
        constraints = [
            models.UniqueConstraint(fields=["email"], name="unique_email")
        ]

    def __str__(self):
        return self.full_name

class Business(models.Model):
    contact = models.ForeignKey(User)
    business_name = models.CharField(max_length=100)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Businesses"
        constraints = [
            models.UniqueConstraint(fields=["business_name"], name="unique_business_name")
        ]

    def __str__(self):
        return self.business_name

