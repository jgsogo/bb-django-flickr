
from django.conf import settings
from django.db.models.signals import class_prepared

def identity(item): return item

use_case_module = getattr(settings, 'FLICKR_USE_CASE', None)

if use_case_module:
    module = __import__(use_case_module, fromlist='*')
    on_class_prepared = getattr(module, 'on_class_prepared', None)
    flickr_oauth_view_decorator = getattr(module, 'flickr_oauth_view_decorator', identity)
    flickr_sync_command_decorator = getattr(module, 'flickr_sync_command_decorator', identity)

    if on_class_prepared:
        class_prepared.connect(on_class_prepared)

else:

    flickr_oauth_view_decorator = identity
    flickr_sync_command_decorator = identity

