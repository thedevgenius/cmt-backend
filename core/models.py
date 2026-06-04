from django.db import models
from django.utils.translation import gettext_lazy as _
from .utils import generate_unique_slug

# Create your models here.
class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created_at`` and ``updated_at`` fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AutoSlugMixin(models.Model):
    """
    An abstract base class that provides an auto-generated, unique slug field.
    Child models MUST define a 'SLUG_SOURCE_FIELD' property (e.g., 'title' or 'name').
    """
    slug = models.SlugField(_("Slug"), max_length=150, unique=True, blank=True, help_text=_("Used for URLs. Auto-generated if left blank."))

    # Set this in your child classes to tell the mixin which field to slugify
    SLUG_SOURCE_FIELD = 'name' 

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Only generate a slug if one doesn't exist
        if not self.slug:
            # Dynamically get the value of the field specified in SLUG_SOURCE_FIELD
            source_text = getattr(self, self.SLUG_SOURCE_FIELD, '')
            self.slug = generate_unique_slug(self, source_text, slug_field_name='slug')
            
        super().save(*args, **kwargs)