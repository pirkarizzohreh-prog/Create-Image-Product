from django.contrib import admin

from .models import Batch, ProductImage


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "default_mode", "image_count", "created_at"]
    search_fields = ["name", "owner__email"]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ["original_filename", "batch", "uploaded_by", "effective_mode", "created_at"]
    search_fields = ["original_filename", "sku", "product_name"]
