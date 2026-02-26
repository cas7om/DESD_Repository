from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import Prefetch
from django.contrib.auth.hashers import make_password, check_password
from functools import wraps


from .models import (
    User,
    Role, UserRole,
    Address, UserAddress,
    Business,
)
from .forms import (
    CustomerRegistrationForm,
    ProducerRegistrationForm,
    AdminRegistrationForm,
    LoginForm,
)


# -----------------------------
# Simple session auth (custom user model)
# -----------------------------
SESSION_USER_ID_KEY = "auth_user_id"

def login_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not _current_user_id(request):
            messages.error(request, "Please log in first.")
            return redirect("accounts:login")
        return view_func(request, *args, **kwargs)
    return _wrapped


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user_id = request.session.get(SESSION_USER_ID_KEY)
        user = User.objects.filter(id=user_id).first()

        if not user:
            messages.error(request, "Please log in first.")
            return redirect("accounts:login")

        if not user.has_role("Admin"):
            messages.error(request, "You do not have permission to access this page.")
            return redirect("accounts:accounts_home")

        return view_func(request, *args, **kwargs)

    return _wrapped


def _login_user(request, user_id: int, remember_me: bool):
    request.session[SESSION_USER_ID_KEY] = user_id
    # remember_me => 14 days, else session cookie
    request.session.set_expiry(60 * 60 * 24 * 14 if remember_me else 0)


def _logout_user(request):
    request.session.pop(SESSION_USER_ID_KEY, None)


def _current_user_id(request):
    return request.session.get(SESSION_USER_ID_KEY)


def _ensure_lookups():
    for r in ["Customer", "Producer", "CommunityGroup", "Restaurant", "Admin"]:
        Role.objects.get_or_create(name=r)



# region Pages
# Pages
# -----------------------------
def accounts_home(request):
    return render(request, "accounts.html")


#NOt working properly and thats TC-022
@admin_required 
def user_list(request):
    users = (
        User.objects
        .all()
        .order_by("id")
        .prefetch_related(
            "user_roles__role",     # roles via UserRole
            "addresses__address",   # addresses via UserAddress
            "managed_businesses__address",  # businesses user manages + business address
        )
    )
    return render(request, "users/list_user.html", {"users": users})


# TC-002 Customer registration
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
                return render(request, "users/create_customer.html", {"form": form, "action": "Register"})

            user = User.objects.create(
                full_name=cd["full_name"],
                email=cd["email"],
                phone_no=cd["phone_no"],
                password_hash=make_password(cd["password"]),
            )

            customer_role = Role.objects.get(name="Customer")
            UserRole.objects.create(user=user, role=customer_role)

            delivery_addr = Address.objects.create(
                line1=cd["line1"],
                line2=cd.get("line2", "") or "",
                line3=cd.get("line3", "") or "",
                postcode=cd["postcode"],
            )

            UserAddress.objects.create(user=user, address=delivery_addr)

            messages.success(request, "Customer account created successfully. You can now log in.")
            return redirect("accounts:login")
    else:
        form = CustomerRegistrationForm()

    return render(request, "users/create_customer.html", {"form": form, "action": "Register"})

# TC-001 Producer registration
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

            user = User.objects.create(
                full_name=cd["contact_name"],
                email=cd["email"],
                phone_no=cd["phone_no"],
                password_hash=make_password(cd["password"]),
            )

            producer_role = Role.objects.get(name="Producer")
            UserRole.objects.create(user=user, role=producer_role)

            business_addr = Address.objects.create(
                line1=cd["line1"],
                line2=cd.get("line2", "") or "",
                line3=cd.get("line3", "") or "",
                postcode=cd["postcode"],
            )

            UserAddress.objects.create(user=user, address=business_addr)

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

@transaction.atomic
def admin_register(request):
    _ensure_lookups()

    if request.method == "POST":
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            if User.objects.filter(email=cd["email"]).exists():
                form.add_error("email", "This email is already registered.")
                return render(request, "users/create_admin.html", {"form": form, "action": "Register"})

            user = User.objects.create(
                full_name=cd["full_name"],
                email=cd["email"],
                phone_no=cd["phone_no"],
                password_hash=make_password(cd["password"]),
            )

            admin_role = Role.objects.get(name="Admin")
            UserRole.objects.create(user=user, role=admin_role)

            messages.success(request, "Admin account created successfully. You can now log in.")
            return redirect("accounts:login")
    else:
        form = AdminRegistrationForm()

    return render(request, "users/create_admin.html", {"form": form, "action": "Register"})


# TC-022 Login / Logout (session auth)
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
