from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.db import IntegrityError
from django.utils.decorators import method_decorator

from userprofile.forms import UserProfileForm, CustomPasswordChangeForm
from userprofile.models import UserProfile


# Register a new user
def register(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        accept_terms = request.POST.get("accept_terms")  # checkbox

        register_url = reverse('login') + '?tab=register'

        # Basic validations
        if not username or not email or not password1 or not password2:
            messages.error(request, "Please fill out all fields.")
            return redirect(register_url)

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect(register_url)

        if not accept_terms:
            messages.error(request, "You must accept the terms to continue.")
            return redirect(register_url)

        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
            )
        except IntegrityError:
            messages.error(request, "Username already exists.")
            return redirect(register_url)

        # Optional: prevent duplicate emails (if not enforced in model)
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            user.delete()
            messages.error(request, "Email already in use.")
            return redirect(register_url)

        # Log the user in
        user = authenticate(request, username=username, password=password1)
        if user:
            login(request, user)
            return redirect("dashboard:dashboard")

        messages.success(request, "Account created. Please sign in.")
        return redirect("login" if "login" in reverse.__code__.co_names else "/")

    # GET -> redirect to login page with register tab
    return redirect(reverse('login') + '?tab=register')


# Edit userprofile
@login_required
def edit_profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)

        if form.is_valid():
            form.save()

            return redirect('userprofile:account')

    else:
        form = UserProfileForm(instance=user_profile)

    return render(request, 'userprofile/edit_profile.html', {
        'form': form
    })


# Account
@login_required
def user_account(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    # Renders the current user's account page
    context = {
        "user": request.user,
        "user_profile": user_profile,
    }
    return render(request, "userprofile/account.html", context)


# Change password
@method_decorator(login_required, name='dispatch')
class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'userprofile/change_password.html'
    success_url = reverse_lazy('userprofile:account')

    def form_valid(self, form):
        messages.success(self.request, 'Your password was successfully updated!')
        return super().form_valid(form)


# Logout
def my_logout(request):
    logout(request)
    return redirect('index')

# Delete account
@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account has been deleted.')
        return redirect('index')

    return render(request, 'userprofile/delete_account.html')