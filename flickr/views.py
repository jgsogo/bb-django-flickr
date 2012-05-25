from bunch import bunchify
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.utils import simplejson
from django.views.generic.list_detail import object_list
from flickr.api import FlickrApi, FlickrUnauthorizedCall
from flickr.models import FlickrAccount, Photo, PhotoSet


FLICKR_KEY = getattr(settings, 'FLICKR_KEY', None)
FLICKR_SECRET = getattr(settings, 'FLICKR_SECRET', None)
PERMS = getattr(settings, 'FLICKR_PERMS', None)


def oauth(request):
    token = None
    api = FlickrApi(FLICKR_KEY, FLICKR_SECRET)
    url = api.auth_url(request, perms=PERMS, callback= request.build_absolute_uri(reverse('flickr_complete')) )
    return HttpResponseRedirect(url)

def oauth_access(request):
    api = FlickrApi(FLICKR_KEY, FLICKR_SECRET)
    data = api.access_token( request )
    if data:
        data = bunchify(data)
        nsid = data.oauth.user.nsid
        fs, created = FlickrAccount.objects.get_or_create(nsid=nsid)
        fs.token = data.token
        fs.username = data.oauth.user.username
        fs.full_name = data.oauth.user.fullname
        fs.perms = data.oauth.perms._content
        fs.save()
        return HttpResponseRedirect(reverse('flickr_auth_validate', kwargs={'nsid' : fs.nsid } ) )
    raise Exception, 'Ups! No data...'

def oauth_validate(request, nsid):
    flickr_account = FlickrAccount.objects.get(nsid=nsid)
    token = flickr_account.token
    api = FlickrApi(FLICKR_KEY, FLICKR_SECRET, token, fallback=False)
    try:
        data = api.get('flickr.test.login')
    except:
        flickr_account.token = None
        flickr_account.perms = None
        flickr_account.save()
        return HttpResponseRedirect(reverse('flickr_auth'))
    return render_to_response('flickr/auth_ok.html', {'token' : token}, context_instance=RequestContext(request))


def index(request, user_id=1):
    photos = Photo.objects.public()
    photosets = PhotoSet.objects.all()
    return object_list(request,
        queryset = photos,
        paginate_by = 10,
        extra_context = { 'photosets': photosets },
        template_object_name = 'photo',
        template_name = 'flickr/index.html'
        )


def photo(request, flickr_id):
    try:
        photo = Photo.objects.get(flickr_id=flickr_id)
    except Photo.DoesNotExist:
        photo = get_object_or_404(Photo, pk=flickr_id)
    return render_to_response("flickr/photo_page.html", { 'photo': photo }, context_instance=RequestContext(request))


def photoset(request, flickr_id):
    photoset = get_object_or_404(PhotoSet, flickr_id=flickr_id)
    photos = Photo.objects.public(photoset__id__in=[photoset.id,])
    photosets = PhotoSet.objects.all()
    return object_list(request,
        queryset = photos,
        paginate_by = 10,
        extra_context = { 'photoset': photoset, 'photosets': photosets },
        template_object_name = 'photo',
        template_name = 'flickr/index.html'
        )


def method_call(request, method, nsid=None):
    api = FlickrApi(FLICKR_KEY, FLICKR_SECRET)
    if nsid:
        api.token = FlickrAccount.objects.get(nsid=nsid).token
        auth = True
    else:
        auth = False
    data = api.get(method, auth=auth, photo_id='6110054503')
    return HttpResponse(simplejson.dumps(data))
