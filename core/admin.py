from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Document, Pricing, Order

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'original_name', 'user', 'file_type',
        'status', 'uploaded_at', 'size'
    ]
    list_filter = ['file_type', 'status', 'uploaded_at']
    search_fields = ['original_name', 'user__username']
    readonly_fields = ['uploaded_at', 'processed_at']
    list_per_page = 20

@admin.register(Pricing)
class PricingAdmin(admin.ModelAdmin):
    list_display = [
        'service_name', 'price_per_unit',
        'unit_type', 'is_active'
    ]
    list_filter = ['is_active', 'unit_type']
    search_fields = ['service_name']
    list_editable = ['is_active']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'document', 'status',
        'total_price', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'document__original_name',
        'user__username'
    ]
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20


admin.site.unregister(User)
admin.site.register(User, UserAdmin)