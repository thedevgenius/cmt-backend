from django.contrib import admin
from .models import State, City


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'slug', 'pincode_prefix')
    search_fields = ('name', 'code')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'slug', 'pincode_prefix')
    search_fields = ('name', 'state__name')
    list_filter = ('state',)
    prepopulated_fields = {'slug': ('name',)}
