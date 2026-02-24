from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.hashers import make_password, check_password

from .models import (
    User,
    Role, UserRole,
    AddressType, Address, UserAddress,
    Business,
)
from .forms import (
    CustomerRegistrationForm,
    ProducerRegistrationForm,
    LoginForm,
)


# -----------------------------
# Simple session auth (custom user model)
# -----------------------------
SESSION_USER_ID_KEY = "auth_user_id"


def _login_user(request, user_id: int, remember_me: bool):
    request.session[SESSION_USER_ID_KEY] = user_id
    # remember_me => 14 days, else session cookie
    request.session.set_expiry(60 * 60 * 24 * 14 if remember_me else 0)


def _logout_user(request):
    request.session.pop(SESSION_USER_ID_KEY, None)


def _current_user_id(request):
    return request.session.get(SESSION_USER_ID_KEY)


def _ensure_lookups():
    # Roles (as per TC-022)
    for r in ["Customer", "Producer", "CommunityGroup", "Restaurant", "Admin"]:
        Role.objects.get_or_create(name=r)

    # Address types
    AddressType.objects.get_or_create(name="DELIVERY")
    AddressType.objects.get_or_create(name="BUSINESS")


# -----------------------------
# Pages
# -----------------------------
def accounts_home(request):
    # You already have accounts.html at app template root
    return render(request, "accounts.html")


def user_list(request):
    users = User.objects.all().order_by("id")
    return render(request, "users/list_user.html", {"users": users})


# -----------------------------
# TC-002 Customer registration
# Uses template: users/create_user.html (your existing file)
# -----------------------------
@transaction.atomic
def customer_register(request):
    _ensure_lookups()

    if request.method == "POST":
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            # enforce unique email
            if User.objects.filter(email=cd["email"]).exists():
                form.add_error("email", "This email is already registered.")
                return render(request, "users/create_user.html", {"form": form, "action": "Register"})

            # 1) Create user
            user = User.objects.create(
                full_name=cd["full_name"],
                email=cd["email"],
                phone_no=cd["phone_no"],
                password_hash=make_password(cd["password"]),
            )

            # 2) Assign customer role
            customer_role = Role.objects.get(name="Customer")
            UserRole.objects.create(user=user, role=customer_role)

            # 3) Create delivery address
            delivery_addr = Address.objects.create(
                line1=cd["line1"],
                line2=cd.get("line2", "") or "",
                line3=cd.get("line3", "") or "",
                postcode=cd["postcode"],
            )

            # 4) Link address as DELIVERY
            delivery_type = AddressType.objects.get(name="DELIVERY")
            UserAddress.objects.create(user=user, address_type=delivery_type, address=delivery_addr)

            messages.success(request, "Customer account created successfully. You can now log in.")
            return redirect("accounts:login")
    else:
        form = CustomerRegistrationForm()

    return render(request, "users/create_user.html", {"form": form, "action": "Register"})


# -----------------------------
# TC-001 Producer registration
# Uses template: users/create_producer.html (create this file)
# -----------------------------
@transaction.atomic
def producer_register(request):
    _ensure_lookups()

    if request.method == "POST":
        form = ProducerRegistrationForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            if User.objects.filter(email=cd["email"]).exists():
                form.add_error("email", "This email is already registered.")
                return render(request, "users/create_producer.html", {"form": form, "action": "Register"})

            # 1) Create user (contact person)
            user = User.objects.create(
                full_name=cd["contact_name"],
                email=cd["email"],
                phone_no=cd["phone_no"],
                password_hash=make_password(cd["password"]),
            )

            # 2) Assign producer role
            producer_role = Role.objects.get(name="Producer")
            UserRole.objects.create(user=user, role=producer_role)

            # 3) Create business address
            business_addr = Address.objects.create(
                line1=cd["line1"],
                line2=cd.get("line2", "") or "",
                line3=cd.get("line3", "") or "",
                postcode=cd["postcode"],
            )

            # 4) Link address to user as BUSINESS
            business_type = AddressType.objects.get(name="BUSINESS")
            UserAddress.objects.create(user=user, address_type=business_type, address=business_addr)

            # 5) Create business referencing contact_user + business address
            Business.objects.create(
                business_name=cd["business_name"],
                address=business_addr,
                contact_user=user,
            )

            messages.success(request, "Producer account created successfully. You can now log in.")
            return redirect("accounts:login")
    else:
        form = ProducerRegistrationForm()

    return render(request, "users/create_producer.html", {"form": form, "action": "Register"})


# -----------------------------
# TC-022 Login / Logout (session auth)
# Uses template: users/login.html (recommended)
# -----------------------------
def login_view(request):
    _ensure_lookups()

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            user = User.objects.filter(email=cd["email"]).first()

            # Generic error message (do not reveal if account exists)
            if not user or not check_password(cd["password"], user.password_hash):
                messages.error(request, "Invalid email or password.")
                return render(request, "users/login.html", {"form": form})

            _login_user(request, user.id, remember_me=cd.get("remember_me", False))
            messages.success(request, "Logged in successfully.")
            return redirect("accounts:accounts_home")
    else:
        form = LoginForm()

    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    _logout_user(request)
    messages.success(request, "Logged out.")
    return redirect("accounts:login")


# -----------------------------
# Keep your old create_user if you still want an admin-style manual add
# (optional) – but it won’t create business/address links automatically.
# -----------------------------
def user_create(request):
    """
    OPTIONAL: keep only if you want a basic CRUD 'create user' page.
    It does NOT satisfy TC-001/TC-002 because it doesn't create address/business/roles.
    """
    from .forms import UserForm  # keep your existing form

    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.full_name} created successfully!")
            return redirect("accounts:user_list")
    else:
        form = UserForm()

    return render(request, "users/create_user.html", {"form": form, "action": "Create"})