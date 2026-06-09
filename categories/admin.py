from django.contrib import admin
from .models import Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # -----------------------------------------------------------
    # 1. LIST VIEW CONFIGURATION (What you see on the main table)
    # -----------------------------------------------------------
    list_display = ('name', 'parent', 'is_active', 'is_featured', 'sort_order', 'updated_at')
    list_editable = ('is_active', 'is_featured', 'sort_order')
    
    list_filter = ('is_active', 'is_featured')
    search_fields = ('name', 'description', 'slug', 'meta_title')
    autocomplete_fields = ['parent']
    ordering = ('sort_order', 'name')
    list_per_page = 50

    # -----------------------------------------------------------
    # 2. EDIT/ADD VIEW CONFIGURATION (Separated by sections)
    # -----------------------------------------------------------
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description'),
            'classes': ('wide',)
        }),
        ('Hierarchy', {
            'fields': ('parent',),
            'description': 'Select a parent category if this is a sub-category. Leave blank for top-level categories.'
        }),
        # ('Media', {
        #     'fields': ('icon',),
        # }),
        ('Visibility & Organization', {
            'fields': ('is_active', 'is_featured', 'sort_order'),
            'description': 'Control how and where this category appears in the Next.js PWA.',
            # 'classes': ('collapse',), # Makes this section collapsible to save screen space
        }),
        ('SEO & Routing', {
            'fields': ('slug', 'meta_title', 'meta_description'),
            'description': 'Crucial for Next.js Server-Side Rendering (SSR). The slug will auto-generate if left blank.',
            # 'classes': ('collapse',), 
        }),
    )

    # Optional: If you want to automatically populate the slug as the admin types the name.
    # Note: Because we use AutoSlugMixin, this isn't strictly necessary, but it provides
    # a nice visual cue for the admin user before they hit "Save".
    prepopulated_fields = {'slug': ('name',)}