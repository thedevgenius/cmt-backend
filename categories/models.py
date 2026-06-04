from django.db import models
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel, AutoSlugMixin

class Category(TimeStampedModel, AutoSlugMixin):
    """
    Hierarchical Category model for Business Directory and Services.
    """
    name = models.CharField(_("Category Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True, null=True)
    
    # Hierarchical Structure
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True, 
        related_name='children',
        help_text=_("Select a parent category to make this a sub-category.")
    )
    
    # UI and Media
    # image = models.ImageField(
    #     _("Icon"),
    #     upload_to='category_icons/%Y/%m/', 
    #     blank=True, 
    #     null=True,
    #     validators=[FileExtensionValidator(['svg', 'png', 'jpg', 'jpeg', 'webp'])],
    #     help_text=_("Upload a scalable vector graphic (SVG) or WebP for optimal PWA performance.")
    # )
    
    # Control Fields
    is_active = models.BooleanField(_("Active"), default=True, help_text=_("Toggle to hide/show this category globally."))
    is_featured = models.BooleanField(_("Featured"), default=False, help_text=_("Highlight this category on the homepage."))
    sort_order = models.PositiveIntegerField(_("Sort Order"), default=0, help_text=_("Lower numbers appear first."))

    # SEO Metadata (Crucial for Next.js SSR)
    meta_title = models.CharField(_("Meta Title"), max_length=150, blank=True, help_text=_("SEO title. Defaults to category name if blank."))
    meta_description = models.CharField(_("Meta Description"), max_length=255, blank=True, help_text=_("SEO description for search engines."))

    SLUG_SOURCE_FIELD = 'name'

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['parent']),
        ]
        constraints = [
            # Prevents creating two sub-categories with the exact same name under the same parent
            models.UniqueConstraint(
                fields=['parent', 'name'], 
                name='unique_category_per_parent'
            )
        ]

    def save(self, *args, **kwargs):
        # Fallback for meta title
        if not self.meta_title:
            self.meta_title = self.name
            
        super().save(*args, **kwargs)

    def __str__(self):
        # Displays the full path in the Django Admin (e.g., "Home Services > Plumbing")
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' -> '.join(full_path[::-1])

    def get_descendants(self):
        """
        Utility method to get all child categories recursively.
        Useful for filtering businesses by a parent category.
        """
        descendants = []
        for child in self.children.filter(is_active=True):
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants