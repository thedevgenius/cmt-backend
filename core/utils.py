from django.utils.text import slugify

def generate_unique_slug(instance, source_text, slug_field_name='slug'):
    """
    Generates a unique slug for a Django model instance.
    
    :param instance: The model instance (e.g., Category, Business)
    :param source_text: The string to be slugified (e.g., instance.name)
    :param slug_field_name: The name of the slug field on the model
    :return: A unique slug string
    """
    base_slug = slugify(source_text)
    
    # Fallback if the source text is empty or contains no slugifiable characters
    if not base_slug:
        base_slug = "item"

    slug = base_slug
    model_class = instance.__class__
    
    # Exclude the current instance if it's already in the database (being updated)
    queryset = model_class.objects.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
        
    # Increment a counter until a unique slug is found
    counter = 1
    while queryset.filter(**{slug_field_name: slug}).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
        
    return slug