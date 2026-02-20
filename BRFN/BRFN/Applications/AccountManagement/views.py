from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count
from .models import User
from .forms import UserForm

def accounts_home(request):
    return render(request, "accounts.html")

def user_list(request):
    users = User.objects.all()
    context = {
        'users': users
    }
    return render(request, 'users/list_user.html', context)


def user_create(request):

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.get_full_name()} created successfully!')
            return redirect('accounts:user_list')
    else:
        form = UserForm()

    context = {
        'form': form,
        'action': 'Create'
    }
    return render(request, 'users/create_user.html', context)