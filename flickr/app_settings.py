
from django.conf import settings

FLICKR_KEY = getattr(settings, 'FLICKR_KEY', None)
FLICKR_SECRET = getattr(settings, 'FLICKR_SECRET', None)
FLICKR_STORE_SIZES = getattr(settings, 'FLICKR_STORE_SIZES', True)
FLICKR_APP_PERMS = getattr(settings, 'FLICKR_APP_PERMS', None)
FLICKR_PHOTO_PIPELINE = getattr(settings, 'FLICKR_PHOTO_PIPELINE', None)
