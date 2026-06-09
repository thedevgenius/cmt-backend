from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Category

@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def invalidate_category_cache(sender, instance, **kwargs):
    """
    Clears all Redis caches related to categories when data changes.
    """
    # Delete the static featured categories cache (from your previous setup)
    cache.delete('featured_categories_list')
    cache.delete('category_scroll_spy_tree')
    
    # Delete ALL dynamically generated list caches using a wildcard.
    cache.delete_pattern('category_list_query_*')