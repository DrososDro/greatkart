from django.contrib import admin
from .models import Cart, CartItems

# Register your models here.


class CartItemsAdmin(admin.ModelAdmin):
    list_display = ("product", "cart", "quantity", "is_active")


admin.site.register(Cart)
admin.site.register(CartItems, CartItemsAdmin)
