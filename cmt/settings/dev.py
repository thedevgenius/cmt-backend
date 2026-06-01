from .base import *



# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://comynity.com",
    "http://10.74.154.149:3000"
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "https://comynity.com",
    "http://10.74.154.149:3000"
]