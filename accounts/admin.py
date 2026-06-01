from django.contrib import admin
from .models import User

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('phone', 'full_name', 'email', 'is_staff', 'is_active')
    search_fields = ('phone', 'full_name', 'email')
    ordering = ('-date_joined',)
    
    # Optional: Define fieldsets so the admin detail page looks clean
    fieldsets = (
        ('Personal Info', {'fields': ('phone', 'full_name', 'email')}),
        ('Permissions', {'fields': ('role', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('last_login', 'date_joined')