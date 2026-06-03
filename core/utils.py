from django.utils.text import slugify

def generate_unique_slug(instance, base_text, slug_field_name='slug'):
    """
    Generates a unique slug for a given Django model instance.
    
    :param instance: The model instance (e.g., self)
    :param base_text: The string to slugify (usually the title or name)
    :param slug_field_name: The name of the slug field on the model (default: 'slug')
    :return: A unique slug string
    """
    # 1. Create the initial base slug
    original_slug = slugify(base_text)
    unique_slug = original_slug
    
    # 2. Get the model class of the instance
    model_class = instance.__class__
    
    # 3. Create a base QuerySet that excludes the current instance (if it already exists)
    # This prevents the object from clashing with its own current slug during an update.
    qs = model_class.objects.all()
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)
        
    # 4. Check for duplicates and increment if necessary
    extension = 2
    while qs.filter(**{slug_field_name: unique_slug}).exists():
        unique_slug = f"{original_slug}-{extension}"
        extension += 1
        
    return unique_slug