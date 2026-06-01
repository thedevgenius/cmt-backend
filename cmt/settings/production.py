from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    "comynity.com",
    "www.comynity.com"
]

SECURE_SSL_REDIRECT = True
MIDDLEWARE.insert(
    2,
    "whitenoise.middleware.WhiteNoiseMiddleware"
)

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)