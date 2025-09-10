from django.contrib import admin
from .models import User, Farmer


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
	list_display = ("username", "email", "role", "is_active", "last_login")
	search_fields = ("username", "email")
	list_filter = ("role", "is_active")


@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
	list_display = ("user", "full_name", "email", "phone", "created_date")
	search_fields = ("full_name", "email", "phone")

# Register your models here.
