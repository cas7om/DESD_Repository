from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from config.constants import SESSION_USER_ID_KEY
from applications.account_management.models import User


def _current_user_id(request):
    return request.session.get(SESSION_USER_ID_KEY)


def _current_user(request):
    user_id = _current_user_id(request)
    if not user_id:
        return None
    return User.objects.filter(id=user_id).first()


def login_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = _current_user(request)
        if not user:
            messages.error(request, "Please log in first.")
            return redirect("accounts:login")
        return view_func(request, *args, **kwargs)
    return _wrapped


def roles_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = _current_user(request)

            if not user:
                messages.error(request, "Please log in first.")
                return redirect("accounts:login")

            if not any(user.has_role(role) for role in allowed_roles):
                messages.error(request, "You do not have permission to access this page.")
                return redirect("accounts:accounts_home")

            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def admin_required(view_func):
    return roles_required("Admin")(view_func)


def producer_required(view_func):
    return roles_required("Producer")(view_func)