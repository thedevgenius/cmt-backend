import os
from django.db import models
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from storages.backends.s3boto3 import S3Boto3Storage
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image

from core.models import TimeStampedModel, AutoSlugMixin

r2_storage = S3Boto3Storage()

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
    image = models.ImageField(
        _("Image"),
        upload_to='category_images/', 
        storage=r2_storage,
        blank=True, 
        null=True,
        validators=[FileExtensionValidator(['svg', 'png', 'jpg', 'jpeg', 'webp'])],
        help_text=_("Upload a scalable vector graphic (SVG) or WebP for optimal PWA performance.")
    )
    
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

        if self.image and hasattr(self.image, 'file') and not self.image.name.endswith('.webp'):
            self.image = self._process_and_convert_image(self.image, max_width=768, quality=85)
            
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
    
    def _process_and_convert_image(self, image_field, max_width, quality):
        """
        Helper method to resize an image, compress it, convert it to WebP format,
        and handle everything purely in memory.
        """
        # Open the uploaded image file using Pillow
        img = Image.open(image_field)

        # Convert image color mode to RGB (WebP doesn't support RGBA/transparency variations perfectly in all old EXIFs)
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            # Keep alpha channel if transparent, otherwise convert to solid RGB
            background = Image.new("RGBA", img.size, (255, 255, 255, 0))
            background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            img = background.convert("RGB")
        else:
            img = img.convert("RGB")

        # Resize the image proportionally if it exceeds our production max_width boundaries
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int(float(img.height) * float(ratio))
            # Resampling with Resampling.LANCZOS ensures high-quality downscaling
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        # Save the altered image to a memory buffer instead of disk
        buffer = BytesIO()
        img.save(buffer, format="WEBP", quality=quality, optimize=True)
        buffer.seek(0)

        # Change the file extension name to .webp so django-storages sends the proper Content-Type header to R2
        original_name = os.path.splitext(image_field.name)[0]
        new_filename = f"{original_name}.webp"

        # Return a new Django ContentFile object ready for R2 streaming
        return ContentFile(buffer.read(), name=new_filename)