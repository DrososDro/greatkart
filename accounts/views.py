# django imports
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib import auth
from django.contrib.auth.decorators import login_required

from orders.models import Order, OrderProduct

# my imports
from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from carts.models import Cart, CartItems
from carts.views import _cart_id
import requests

# verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

# Create your views here.


def register(request):
    form = RegistrationForm()

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.username = user.email.split("@")[0]
            user.save()
            # Create a user profile
            profile = UserProfile()
            profile.user_id = user.id
            profile.profile_picture = "default/default-user.png"
            profile.save()
            # user activation
            current_site = get_current_site(request)
            mail_subject = "please activate your account"
            message = render_to_string(
                "accounts/account_verification_email.html",
                {
                    "user": user,
                    "domain": current_site,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                },
            )
            to_email = user.email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            return redirect(
                "/account/login/?command=verification&email=" + user.email,
            )

    context = {
        "form": form,
    }
    return render(request, "accounts/register.html", context)


def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = auth.authenticate(username=email, password=password)
        if user:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))

                is_cart_item_exists = CartItems.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_ites = CartItems.objects.filter(cart=cart)

                    profuct_variation = []
                    for item in cart_ites:
                        variation = item.variation.all()
                        profuct_variation.append(list(variation))

                    cart_item = CartItems.objects.filter(
                        user=user,
                    )

                    ex_var_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variation.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)

                    for pr in profuct_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItems.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_ites = CartItems.objects.filter(cart=cart)

                            for item in cart_ites:
                                item.user = user
                                item.save()

            except Exception:
                pass
            auth.login(request, user)
            messages.success(request, "You are now Log In")
            # here goes the requests
            url = request.META.get("HTTP_REFERER")
            try:
                query = requests.utils.urlparse(url).query
                print(query)
                params = dict(x.split("=") for x in query.split("&"))
                print(params)
                if "next" in params:
                    nextpage = params["next"]
                    return redirect(nextpage)
            except Exception:
                return redirect("dashboard")
        else:
            messages.error(request, "Invalid login credentials")
            return redirect("login")
    return render(request, "accounts/login.html")


@login_required(login_url="login")
def logout(request):
    auth.logout(request)
    messages.success(request, "You log out!")

    return redirect("login")


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(
            request,
            "Congratulations! Your Account is activated!",
        )
        return redirect("login")
    else:
        messages.error(request, "Invalid activation link")
        return redirect("register")


@login_required(login_url="login")
def dashboard(request):
    orders = Order.objects.order_by("-created_at").filter(
        user_id=request.user.id, is_ordered=True
    )
    orders_count = orders.count()
    context = {
        "orders_count": orders_count,
    }
    return render(request, "accounts/dashboard.html", context)


def forgotPassword(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = Account.objects.get(email=email)
            current_site = get_current_site(request)
            mail_subject = "Reset Password"
            message = render_to_string(
                "accounts/reset_password_email.html",
                {
                    "user": user,
                    "domain": current_site,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                },
            )
            to_email = user.email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(
                request, f"Password reset email sent to {user.email} address"
            )
            return redirect("forgotPassword")

        except Account.DoesNotExist:
            messages.error(request, "Account does not exists!")
            return redirect("login")
    return render(request, "accounts/forgot_password.html")


def reset_password_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session["uid"] = uid
        messages.success(request, "Please reset your password")
        return redirect("resetPassword")
    else:
        messages.error(request, "This link has expired")
        return redirect("login")


def reset_password(request):
    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        if password == confirm_password:
            uid = request.session.get("uid")
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()

            messages.success(request, "password reset successful ")
            return redirect("login")
        else:
            messages.error(request, "The password does not match")
            return redirect("resetPassword")

    return render(request, "accounts/reset_password.html")


@login_required(login_url="login")
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by(
        "-created_at"
    )
    context = {
        "orders": orders,
    }
    return render(request, "accounts/my_orders.html", context)


@login_required(login_url="login")
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for i in order_detail:
        subtotal += i.product_price * i.quantity

    context = {
        "order_detail": order_detail,
        "order": order,
        "subtotal": subtotal,
    }
    return render(request, "accounts/order_detail.html", context)


@login_required(login_url="login")
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    print(userprofile)
    user_form = UserForm(instance=request.user)
    profile_form = UserProfileForm(instance=userprofile)
    if request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(
            request.POST, request.FILES, instance=userprofile
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("edit_profile")
    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "userprofile": userprofile,
    }
    return render(request, "accounts/edit_profile.html", context)


@login_required(login_url="login")
def change_password(request):
    if request.method == "POST":
        current_password = request.POST["current_password"]
        new_password = request.POST["new_password"]
        confirm_password = request.POST["confirm_password"]

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                # auth.logout(request)
                messages.success(request, "Password updated successfully.")
                return redirect("change_password")
            else:
                messages.error(request, "Please enter valid current password")
                return redirect("change_password")
        else:
            messages.error(request, "Password does not match!")
            return redirect("change_password")
    return render(request, "accounts/change_password.html")
