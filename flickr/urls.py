from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^auth/$', "flickr.views.oauth", name="flickr_auth"),
    url(r'^auth/validate/(?P<nsid>[\w@]+)/$', "flickr.views.oauth_validate", name="flickr_auth_validate"),
    url(r'^auth/complete/$', "flickr.views.oauth_access", name="flickr_complete"),

    url(r'^method/(?P<method>.*)/$', "flickr.views.method_call", name="flickr_method"),
    url(r'^set/(?P<flickr_id>.*)/$', "flickr.views.photoset", name="flickr_photoset"),
    url(r'^photo/(?P<flickr_id>.*)/$', "flickr.views.photo", name="flickr_photo"),
    url(r'^$', "flickr.views.index", name="flickr_index"),
)


