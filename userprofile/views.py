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

        # Basic validations
        if not username or not email or not password1 or not password2:
            messages.error(request, "Please fill out all fields.")
            return render(request, "userprofile/register.html")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "userprofile/register.html")

        if not accept_terms:
            messages.error(request, "You must accept the terms to continue.")
            return render(request, "userprofile/register.html")

        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
            )
        except IntegrityError:
            messages.error(request, "Username already exists.")
            return render(request, "userprofile/register.html")

        # Optional: prevent duplicate emails (if not enforced in model)
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            user.delete()
            messages.error(request, "Email already in use.")
            return render(request, "userprofile/register.html")

        # Log the user in
        user = authenticate(request, username=username, password=password1)
        if user:
            login(request, user)
            return redirect(reverse("dashboard:dashboard") if "dashboard" in reverse.__code__.co_names else "/")

        messages.success(request, "Account created. Please sign in.")
        return redirect("login" if "login" in reverse.__code__.co_names else "/")

    # GET -> render form
    return render(request, "userprofile/register.html")


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
    # Renders the current user's account page
    context = {
        "user": request.user,
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