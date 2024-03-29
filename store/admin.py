from django.contrib import admin
from .models import Product, Variation, ReviewRating


# Register your models here.
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "product_name",
        "price",
        "stock",
        "category",
        "created_date",
        "modified_date",
        "is_available",
    )
    prepopulated_fields = {"slug": ("product_name",)}

    readonly_fields = ("modified_date", "created_date")


admin.site.register(Product, ProductAdmin)
admin.site.register(Variation)
admin.site.register(ReviewRating)
