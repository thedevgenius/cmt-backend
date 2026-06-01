from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    "staging.comynity.com"
]

MIDDLEWARE.insert(
    2,
    "whitenoise.middleware.WhiteNoiseMiddleware"
)

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)