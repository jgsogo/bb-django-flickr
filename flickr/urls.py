from django.conf.urls.defaults import patterns, url

from flickr.views import PhotoSource

urlpatterns = patterns('',
    url(r'^auth/$', "flickr.views.oauth", name="flickr_auth"),
    url(r'^auth/complete/$', "flickr.views.oauth_access", name="flickr_complete"),

    url(r'^auth/deprecated/$', "flickr.views.auth", name="flickr_auth_deprecated"),
    url(r'^flickr-callback/$', "flickr.views.auth", name="flickr_auth_callback"),

    url(r'^method/(?P<method>\w+)/$', "flickr.views.method_call", name="flickr_method"),
    url(r'^set/(?P<flickr_id>\w+)/$', "flickr.views.photoset", name="flickr_photoset"),
    url(r'^photo/(?P<flickr_id>\w+)/$', "flickr.views.photo", name="flickr_photo"),
    url(r'^$', "flickr.views.index", name="flickr_index"),

    # pass through image proxy
    url(r'^photo/(?P<flickr_id>\w+)/link/(?P<size_label>\w+)', PhotoSource.as_view(), name="flickr_photo_safe"),
)


