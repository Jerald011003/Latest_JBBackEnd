from django.contrib import admin
from .models import CustomUser, Transaction, Notification, TopUpRequest, Canteen, FoodCategory, Food, Order, FeaturedFood
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    model = CustomUser
    ordering = ('-date_joined',)
    list_display = ('email', 'phone_number', 'first_name', 'last_name', 'height', 'weight', 'bmi', 'balance', 'is_staff', 'is_superuser')
    list_editable = ('balance',)  # Make 'balance' editable in the list view
    list_filter = ('is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 'balance', 'height', 'weight', 'bmi')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'balance', 'height', 'weight', 'bmi', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'phone_number', 'first_name', 'last_name')
    filter_horizontal = ()

    def save_model(self, request, obj, form, change):
        if obj.height and obj.weight:
            height_in_meters = obj.height / 100
            obj.bmi = round(obj.weight / (height_in_meters ** 2), 2)
        super().save_model(request, obj, form, change)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'amount', 'date')
    list_filter = ('date',)
    search_fields = ('sender__email', 'recipient__email', 'amount')


class TopUpRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_first_name', 'user', 'amount', 'is_approved', 'created_at', 'user_balance')
    list_editable = ('is_approved',)  # Make 'is_approved' editable in the list view
    list_filter = ('is_approved',)    # Optional: Add filters for better searchability
    search_fields = ('user__email',)  # Enable search by user email

    def user_balance(self, obj):
        return obj.user.balance
    user_balance.short_description = 'User Balance'

    def save_model(self, request, obj, form, change):
        # Handle balance update when a top-up request is approved
        if 'is_approved' in form.changed_data and obj.is_approved:
            # Use a transaction to ensure consistency
            from django.db import transaction

            with transaction.atomic():
                user = obj.user
                user.balance += obj.amount
                user.save()
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing objects
            return ('id', 'user', 'amount', 'created_at', 'user_balance')  # Make certain fields read-only
        return super().get_readonly_fields(request, obj)

@admin.register(Canteen)
class CanteenAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'canteen']
    search_fields = ['name', 'canteen__name']
    list_filter = ['canteen']

@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'price', 'category']
    search_fields = ['name', 'category__name', 'category__canteen__name']
    list_filter = ['category', 'category__canteen']

@admin.register(FeaturedFood)
class FeaturedFoodAdmin(admin.ModelAdmin):
    list_display = ['food']
    search_fields = ['food__name']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'food', 'quantity', 'total_price', 'created_at']
    search_fields = ['user__username', 'food__name']
    list_filter = ['created_at', 'food__category', 'food__category__canteen']

admin.site.register(CustomUser, UserAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Notification)
admin.site.register(TopUpRequest, TopUpRequestAdmin)

