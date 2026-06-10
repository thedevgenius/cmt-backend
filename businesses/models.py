import uuid
import pygeohash as pgh
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator

from core.models import TimeStampedModel, AutoSlugMixin # Reusing your abstract mixins
from categories.models import Category # Assuming Category is in the same app
from locations.models import City # Assuming City is in the same app

class Business(TimeStampedModel, AutoSlugMixin):
    """
    Core Business profile for the directory, handling location, categorization, 
    and operational metadata.
    """
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        PENDING = 'PENDING', _('Pending Approval')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        SUSPENDED = 'SUSPENDED', _('Suspended')
    
    class Tier(models.TextChoices):
        BASIC = 'BASIC', 'Basic'
        PRO = 'PRO', 'Professional'
        SPONSORED = 'SPONSORED', 'Sponsored (Top Tier)'

    # -----------------------------------------------------------
    # IDENTITY & OWNERSHIP
    # -----------------------------------------------------------
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='businesses',
        help_text=_("The user who manages this business profile.")
    )
    name = models.CharField(_("Business Name"), max_length=255)
    description = models.TextField(_("About the Business"))
    
    # AutoSlugMixin configuration
    SLUG_SOURCE_FIELD = 'name'

    # A business can belong to multiple categories (e.g., a "Cafe" that is also a "Bakery")
    categories = models.ManyToManyField(
        Category, 
        related_name='businesses',
        limit_choices_to={'is_active': True}
    )
    tier = models.CharField(
        max_length=20, 
        choices=Tier.choices, 
        default=Tier.BASIC,
        db_index=True
    )

    # -----------------------------------------------------------
    # MEDIA
    # -----------------------------------------------------------
    # logo = models.ImageField(upload_to='business_logos/%Y/%m/', blank=True, null=True)
    # cover_image = models.ImageField(upload_to='business_covers/%Y/%m/', blank=True, null=True)

    # -----------------------------------------------------------
    # CONTACT & LOCATION
    # -----------------------------------------------------------
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', 
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    phone_number_2 = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    email = models.EmailField(_("Contact Email"), blank=True)
    website = models.URLField(_("Website URL"), blank=True)

    # Physical Address
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    postal_code = models.CharField(max_length=20)
    
    # Exact Coordinates (Standard Decimal approach as established)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    geohash = models.CharField(max_length=12, db_index=True, blank=True)

    # -----------------------------------------------------------
    # FLEXIBLE METADATA (JSON)
    # -----------------------------------------------------------
    # e.g., {"instagram": "url", "facebook": "url"}
    social_links = models.JSONField(default=dict, blank=True)

    # -----------------------------------------------------------
    # STATUS & DENORMALIZED METRICS
    # -----------------------------------------------------------
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.DRAFT,
        db_index=True
    )
    is_verified = models.BooleanField(
        default=False, 
        help_text=_("Indicates if the business identity has been verified by admins.")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Soft delete flag. Inactive businesses won't appear in listings.")
    )
    
    # Denormalized fields to make list views lightning fast
    average_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(5.00)]
    )
    total_reviews = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _('Business')
        verbose_name_plural = _('Businesses')
        ordering = ['-created_at']
        db_table = 'businesses'
        
        # Highly optimized indexes for common searches and location lookups
        indexes = [
            models.Index(fields=['status', 'is_verified']),
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['city']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Auto-generate the geohash if coordinates exist
        if self.latitude and self.longitude:
            self.geohash = pgh.encode(float(self.latitude), float(self.longitude), precision=12)
        super().save(*args, **kwargs)