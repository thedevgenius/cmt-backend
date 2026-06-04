from django.urls import path
from .views import ReverseGeocodeView, LocationAutocompleteView, PlaceCoordinatesView

urlpatterns = [
    path('geocode/reverse/', ReverseGeocodeView.as_view(), name='reverse_geocode'),
    path('autocomplete/', LocationAutocompleteView.as_view(), name='location_autocomplete'),
    path('coordinates/', PlaceCoordinatesView.as_view(), name='place_coordinates'),
]