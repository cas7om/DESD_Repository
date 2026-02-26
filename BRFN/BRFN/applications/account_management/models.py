from django.db import models

class User(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=150, unique=True)
    phone_no = models.CharField(max_length=20, blank=True)
    password_hash = models.CharField(max_length=300, default="")

    def roles(self):
        return self.user_roles.values_list("role__name", flat=True)

    def has_role(self, role_name: str) -> bool:
        return self.user_roles.filter(role__name=role_name).exists()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["email"], name="uq_email")
        ]

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
        return f"{self.user_id} -> {self.address_id}"


class Business(models.Model):
    business_name = models.CharField(max_length=100, unique=True)
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="businesses")
    contact_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="managed_businesses")

    def __str__(self) -> str:
        return self.business_name