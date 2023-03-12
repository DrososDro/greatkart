from django.shortcuts import redirect, render, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from .models import Product
from category.models import Category

# Create your views here.


def home(request):
    products = Product.objects.all().filter(is_available=True)
    context = {"products": products}
    return render(request, "home.html", context)


def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories)
        product_count = products.count()
    else:
        products = Product.objects.all().filter(is_available=True)
        product_count = products.count()
    context = {"products": products, "product_count": product_count}
    return render(request, "store/store.html", context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(
            category__slug=category_slug, slug=product_slug
        )
    except ObjectDoesNotExist:
        return redirect("store")
    context = {"single_product": single_product}
    return render(request, "store/product_detail.html", context)
