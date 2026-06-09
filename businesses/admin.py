from django.contrib import admin
from .models import Business

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'city', 'status', 'is_verified', 'average_rating', 'created_at')
    list_filter = ('status', 'is_verified', 'city', 'categories')
    search_fields = ('name', 'description', 'email', 'phone_number', 'city', 'slug')
    
    # Crucial: Categories can be huge, so we use autocomplete to prevent UI freezing
    autocomplete_fields = ['owner', 'categories']
    list_editable = ('status', 'is_verified')
    
    readonly_fields = ('average_rating', 'total_reviews', 'view_count')
    horizontal_filters = ('categories',)
    list_per_page = 20

    fieldsets = (
        ('Identity & Ownership', {
            'fields': ('owner', 'name', 'slug', 'description', 'categories')
        }),
        ('Status & Verification', {
            'fields': ('status', 'is_verified')
        }),
        # ('Media', {
        #     'fields': ('logo', 'cover_image')
        # }),
        ('Contact Information', {
            'fields': ('phone_number', 'email', 'website')
        }),
        ('Location Details', {
            'fields': (
                'address_line_1', 'address_line_2', 
                'city', 'postal_code', 
                ('latitude', 'longitude')
            )
        }),
        ('Operating Data & Socials', {
            'fields': ('social_links', ),
            'classes': ('collapse',),
        }),
        ('Metrics (Auto-Calculated)', {
            'fields': ('average_rating', 'total_reviews', 'view_count'),
            'classes': ('collapse',),
        }),
    )