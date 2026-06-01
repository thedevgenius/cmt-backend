import uuid
from django.db import models
from django.core.validators import RegexValidator
from .managers import CustomUserManager
from django.contrib.auth.models import AbstractUser, PermissionsMixin
# Create your models here.
class User(AbstractUser, PermissionsMixin):
    USER_ROLE = (
        ('SA', 'Super Admin'),
        ('BO', 'Business/Page Owner'),
        ('NU', 'User'),
    )
    username = None
    first_name = None
    last_name = None
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', 
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=2, choices=USER_ROLE, default='NU')
    profile_color = models.CharField(max_length=7, default='#FF0000')


    objects = CustomUserManager()

    # Define the unique identifier for authentication
    USERNAME_FIELD = 'phone'
    # Fields required when using `createsuperuser` via command line
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return f"{self.full_name} ({self.phone})"
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        db_table = 'users'
        indexes = [
            models.Index(fields=['phone'], name='phone_idx'),
            models.Index(fields=['full_name'], name='full_name_idx'),
            models.Index(fields=['role'], name='role_idx'),
        ]