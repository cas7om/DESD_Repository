from django.shortcuts import render, redirect
from django.contrib import messages
from functools import wraps
from config.constants import SESSION_USER_ID_KEY
from applications.account_management.models import User

def _current_user_id(request):
    return request.session.get(SESSION_USER_ID_KEY)

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