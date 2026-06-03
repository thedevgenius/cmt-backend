from django.db import models
from core.utils import generate_unique_slug
# Create your models here.
class State(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    pincode_prefix = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'States'
        db_table = 'states'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name, slug_field_name='slug')
        super(State, self).save(*args, **kwargs)


class City(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    pincode_prefix = models.CharField(max_length=100, blank=True, null=True)
    
    
    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ('name', 'state')
        db_table = 'cities'
        verbose_name_plural = 'Cities'
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name, slug_field_name='slug')
        super(City, self).save(*args, **kwargs)