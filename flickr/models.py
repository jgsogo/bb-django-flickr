#!/usr/bin/env python
# encoding: utf-8
from bunch import \
    bunchify #for json.dot.notation instead of json['annoying']['dict']
from datetime import datetime
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.timezone import now
from taggit.managers import TaggableManager
from flickr.flickr_spec import build_photo_url, get_size_from_label, \
                                FLICKR_PHOTO_SIZES, FLICKR_URL_PAGE, FLICKR_PHOTOS_URL,\
                                FLICKR_PROFILE_URL, FLICKR_BUDDY_ICON, FLICKR_BUDDY_ICON_DEFAULT,\
                                FLICKR_SHORT_PHOTO_URL, b58encode

from flickr.app_settings import FLICKR_STORE_SIZES


def ts_to_dt(timestamp):
    return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

def unslash(url):
    return url.replace('\\/','/')


class FlickrUserManager(models.Manager):

    def update_from_json(self, pk, info, **kwargs):
        person = bunchify(info['person'])
        user_data = {'username': person.username._content, 'realname': person.realname._content,
                     'flickr_id': person.id, 'nsid': person.nsid,
                     'iconserver': person.iconserver, 'iconfarm': person.iconfarm, 'path_alias': person.path_alias,
                     'mobileurl': unslash(person.mobileurl._content),
                     'ispro' : person.ispro,
                     'last_sync': now(),
                     }
        return self.filter(pk=pk).update(**dict(user_data.items() + kwargs.items()))


class FlickrUser(models.Model):
    user = models.OneToOneField(User)
    flickr_id = models.CharField(max_length=50, null=True, blank=True)
    nsid = models.CharField(max_length=32)
    username = models.CharField(max_length=64, null=True, blank=True)
    realname = models.CharField(max_length=64, null=True, blank=True)
    mobileurl = models.URLField(max_length=255, null=True, blank=True)
    iconserver = models.CharField(max_length=4, null=True, blank=True)
    iconfarm = models.PositiveSmallIntegerField(null=True, blank=True)
    path_alias = models.CharField(max_length=32, null=True, blank=True)
    ispro = models.BooleanField()

    token = models.CharField(max_length=128, null=True, blank=True)
    perms = models.CharField(max_length=32, null=True, blank=True)
    last_sync = models.DateTimeField(auto_now=True, auto_now_add=True)

    objects = FlickrUserManager()

    class Meta:
        ordering = ['id']

    def __unicode__(self):
        return u"%s" % self.username

    def get_photosurl(self):
        return FLICKR_PHOTOS_URL % {'user-id': self.nsid}
    photosurl = property(get_photosurl)

    def get_profileurl(self):
        return FLICKR_PROFILE_URL % {'user-id': self.nsid}
    profileurl = property(get_profileurl)

    def get_buddy_icon(self):
        if self.iconserver > 0:
            return FLICKR_BUDDY_ICON % {'icon-farm':self.iconfarm, 'icon-server':self.iconserver, 'nsid':self.nsid}
        else:
            return FLICKR_BUDDY_ICON_DEFAULT
    buddyicon = property(get_buddy_icon)


class FlickrModel(models.Model):
    flickr_id = models.CharField(unique=True, db_index=True, max_length=50)
    user = models.ForeignKey(FlickrUser)
    show = models.BooleanField(default=True) #show the photo on your page?
    last_sync = models.DateTimeField(auto_now=True, auto_now_add=True)

    class Meta:
        abstract = True


FLICKR_LICENSES = (
    ('0', 'All Rights Reserved'),
    ('1', 'Attribution-NonCommercial-ShareAlike License'),
    ('2', 'Attribution-NonCommercial License'),
    ('3', 'Attribution-NonCommercial-NoDerivs License'),
    ('4', 'Attribution License'),
    ('5', 'Attribution-ShareAlike License'),
    ('6', 'Attribution-NoDerivs License'),
)


class BigIntegerField(models.IntegerField):
    """
    Defines a PostgreSQL compatible IntegerField needed to prevent 'integer
    out of range' with large numbers.
    """
    def get_internal_type(self):
        return 'BigIntegerField'

    def db_type(self):
        if settings.DATABASE_ENGINE == 'oracle':
            db_type = 'NUMBER(19)'
        else:
            db_type = 'bigint'
        return db_type


class PhotoManager(models.Manager):

    def visible(self, *args, **kwargs):
        return self.get_query_set().filter(show=True).filter(*args, **kwargs)

    def public(self, *args, **kwargs):
        return self.visible(ispublic=1, *args, **kwargs)

    def _prepare_data(self, info, sizes=None, flickr_user=None, exif=None, geo=None):
        photo = bunchify(info['photo'])
        photo_data = {
                  'flickr_id': photo.id, 'server': photo.server,
                  'secret': photo.secret, 'originalsecret': getattr(photo, 'originalsecret', ''), 'farm': photo.farm,
                  'originalformat': getattr(photo, 'originalformat', ''),
                  'title': photo.title._content, 'description': photo.description._content, 'date_taken': photo.dates.taken,
                  'date_posted': ts_to_dt(photo.dates.posted), 'date_updated': ts_to_dt(photo.dates.lastupdate),
                  'date_taken_granularity':  photo.dates.takengranularity,
                  'ispublic': photo.visibility.ispublic, 'isfriend': photo.visibility.isfriend,
                  'isfamily': photo.visibility.isfamily,
                  'license': photo.license, 'tags': photo.tags.tag,
                  'last_sync' : now(),
                  }
        if flickr_user:
            photo_data['user'] = flickr_user

        if sizes:
            size_json = bunchify(sizes['sizes']['size'])
            max_size = size_json[-1]
            if max_size.label=='Original':
                photo_data['ori_width'] = max_size.width
                photo_data['ori_height'] = max_size.height
            photo_data['sizes'] = size_json
        if exif:
            try:
                photo_data['exif_camera'] = exif['photo']['camera']
                for e in bunchify(exif['photo']['exif']):
                    if e.label == 'Exposure':     photo_data['exif_exposure'] = unslash(e.raw._content)
                    if e.label == 'Aperture':     photo_data['exif_aperture'] = unslash(e.clean._content)
                    if e.label == 'ISO Speed':    photo_data['exif_iso'] = e.raw._content
                    if e.label == 'Focal Length': photo_data['exif_focal'] = e.clean._content
                    if e.label == 'Flash':        photo_data['exif_flash'] = e.raw._content
            except KeyError:
                pass
            except AttributeError: # 'e.clean._content'
                pass
        if geo:
            pass
        return photo_data

    def _add_tags(self, obj, tags, override=False):
        try:
            obj.tags.set(*[tag._content for tag in tags])
        except KeyError:
            pass

    def _add_sizes(self, obj, sizes, override=False):
        for size in sizes:
            try:
                photosize = getattr(obj, FLICKR_PHOTO_SIZES[size.label]['label'])
                size.pop('url')
                size.pop('label')
                size.pop('media')
                obj.sizes.filter(pk=photosize.pk).update(**size)
            except:
                pass

    def create_from_json(self, flickr_user, info, sizes, exif=None, geo=None, **kwargs):
        """Create a record for flickr_user"""
        photo_data = self._prepare_data(flickr_user=flickr_user, info=info, sizes=sizes, exif=exif, geo=geo, **kwargs)
        tags = photo_data.pop('tags')
        sizes = photo_data.pop('sizes')
        obj = self.create(**dict(photo_data.items() + kwargs.items()))
        self._add_tags(obj, tags)
        self._add_sizes(obj, sizes)
        return obj

    def update_from_json(self, flickr_id, info, sizes, exif=None, geo=None, update_tags=False, update_sizes=False, **kwargs):
        """Update a record with flickr_id"""
        photo_data = self._prepare_data(info=info, sizes=sizes, exif=exif, geo=geo, **kwargs)
        tags = photo_data.pop('tags')
        sizes = photo_data.pop('sizes')
        result = self.filter(flickr_id=flickr_id).update(**dict(photo_data.items() + kwargs.items()))
        if result == 1:
            obj = self.get(flickr_id=flickr_id)
            if update_tags:
                obj.tags.clear()
                self._add_tags(obj, tags)
            if update_sizes:
                obj.sizes.clear()
                self._add_sizes(obj, sizes)
        return result

    def create_or_update_from_json(self, flickr_user, info, sizes, exif=None, geo=None, **kwargs):
        """Pretty self explanatory"""


class Photo(FlickrModel):

    """http://www.flickr.com/services/api/explore/flickr.photos.getInfo"""

    server = models.PositiveSmallIntegerField()
    farm = models.PositiveSmallIntegerField()
    secret = models.CharField(max_length=10)
    originalsecret = models.CharField(max_length=10)
    originalformat = models.CharField(max_length=4) # TBD: choices?

    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    date_posted = models.DateTimeField(null=True, blank=True)
    date_taken = models.DateTimeField(null=True, blank=True)
    date_taken_granularity = models.PositiveSmallIntegerField(null=True, blank=True)
    date_updated = models.DateTimeField(null=True, blank=True)

    tags = TaggableManager(blank=True)

    """http://www.flickr.com/services/api/explore/flickr.photos.getExif
    Lots of data varying type and values, maybe not fully implemented."""

    exif_camera = models.CharField(max_length=50, null=True, blank=True)
    exif_exposure = models.CharField(max_length=10, null=True, blank=True)
    exif_aperture = models.CharField(max_length=10, null=True, blank=True)
    exif_iso = models.IntegerField(null=True, blank=True)
    exif_focal = models.CharField(max_length=10, null=True, blank=True)
    exif_flash = models.CharField(max_length=20, null=True, blank=True)

    """http://www.flickr.com/services/api/explore/flickr.photos.getPerms"""

    ispublic = models.NullBooleanField()
    isfriend = models.NullBooleanField()
    isfamily = models.NullBooleanField()

    """http://www.flickr.com/services/api/explore/flickr.photos.geo.getLocation"""

    geo_latitude = models.FloatField(null=True, blank=True)
    geo_longitude = models.FloatField(null=True, blank=True)
    geo_accuracy = models.PositiveSmallIntegerField(null=True, blank=True)

    license = models.CharField(max_length=50, choices=FLICKR_LICENSES, default=0)

    objects = PhotoManager()

    class Meta:
        ordering = ('-date_posted', '-date_taken',)
        get_latest_by = 'date_posted'

    def __unicode__(self):
        return u'%s' % self.title

    def get_absolute_url(self):
        return reverse('flickr_photo', args=[self.flickr_id,])

    @models.permalink
    def get_safe_url(self, size_label):
        return ('flickr_photo_safe', (), {'flickr_id':self.flickr_id, 'size_label':size_label})

    """ url_page """
    def get_url_page(self):
        return FLICKR_URL_PAGE % {'user-id': self.user.nsid, 'photo-id':self.flickr_id}
    url_page = property(get_url_page)

    def get_short_url(self):
        return FLICKR_SHORT_PHOTO_URL % { 'short-photo-id' : b58encode(int(self.flickr_id))}
    short_url = property(get_short_url)

    """because 'Model.get_previous_by_FOO(**kwargs) For every DateField and DateTimeField that does not have null=True'"""
    def get_next_by_date_posted(self):
        try:
            return Photo.objects.filter(date_posted__gte=self.date_posted).exclude(flickr_id=self.flickr_id).order_by('date_posted', 'date_taken')[:1].get()
        except:
            pass


    def get_next_public_by_date_posted(self):
        try:
            return Photo.objects.public().filter(date_posted__gte=self.date_posted).exclude(flickr_id=self.flickr_id).order_by('date_posted', 'date_taken')[:1].get()
        except:
            pass


    def get_previous_by_date_posted(self):
        try:
            return Photo.objects.filter(date_posted__lte=self.date_posted).exclude(flickr_id=self.flickr_id).order_by('-date_posted', '-date_taken')[:1].get()
        except:
            pass

    def get_previous_public_by_date_posted(self):
        try:
            return Photo.objects.public().filter(date_posted__lte=self.date_posted).exclude(flickr_id=self.flickr_id).order_by('-date_posted', '-date_taken')[:1].get()
        except:
            pass


    """shortcuts - bringing some sanity"""
    def get_next(self): return self.get_next_public_by_date_posted()
    def get_prev(self): return self.get_previous_public_by_date_posted()




    def get_next_by_date_taken(self):
        try:
            return Photo.objects.filter(date_taken__gte=self.date_taken)[:1].get()
        except:
            pass

    def get_previous_by_date_taken(self):
        try:
            return Photo.objects.filter(date_taken__lte=self.date_taken)[:1].get()
        except:
            pass


    def get_next_in_photoset(self, photoset):
        if not hasattr(self, '_next_in_ps%s' % photoset.flickr_id):
            photo = None
            try:
                if photoset.photos.filter(flickr_id=self.flickr_id).exists():
                    photo = photoset.photos.visible().filter(date_posted__gte=self.date_posted).exclude(flickr_id=self.flickr_id).order_by('date_posted', 'date_taken')[:1].get()
                    print photo
            except:
                pass
            setattr(self, '_next_in_ps%s' % photoset.flickr_id, photo)
        return getattr(self, '_next_in_ps%s' % photoset.flickr_id)


    def get_previous_in_photoset(self, photoset):
        if not hasattr(self, '_previous_in_ps%s' % photoset.flickr_id):
            photo = None
            try:
                if photoset.photos.filter(flickr_id=self.flickr_id).exists():
                    photo = photoset.photos.visible().filter(date_posted__lte=self.date_posted).exclude(flickr_id=self.flickr_id).order_by('-date_posted', '-date_taken')[:1].get()
            except:
                pass
            setattr(self, '_previous_in_ps%s' % photoset.flickr_id, photo)
        return getattr(self, '_previous_in_ps%s' % photoset.flickr_id)


"""
Photo model needs sizes property, it will depend on configuration
"""
if not FLICKR_STORE_SIZES:
    class PhotoSize(object):
        """
        PhotoSize 'model' for no-sizes-storage use case. Only builds
        urls, no info about sizes is provided
        """
        width = None
        height = None
        def __init__(self, photo, size):
            self.photo = photo
            self.size = size
            self.label = size['label']
            if self.label == 'ori':
                self.secret = self.photo.originalsecret
                self.format = self.photo.originalformat
                self.is_ori = True
            else:
                self.secret = self.photo.secret
                self.format = 'jpg'
                self.is_ori = False

        def _size_available(self):
            try:
                return self.secret != ''
            except:
                return False
        is_available = property(_size_available)

        def _get_source(self):
            if self.is_available:
                return build_photo_url(self.photo.farm, self.photo.server, self.photo.flickr_id, self.secret, self.size, self.format)
            else: return None
        source = property(_get_source)


    for key,size in FLICKR_PHOTO_SIZES.items():
        label = size.get('label', None)
        setattr(Photo, label, property(lambda self, size=size: PhotoSize(self, size=size)))


    class PhotoSizesManagerProxy(models.Manager):
        """ Custom manager to keep compatibility with FLICKR_STORAGE_SIZES """
        def __init__(self, *args, **kwargs):
            pass
        def contribute_to_class(self, model, name):
            pass
        def get_query_set(self):
            return self.get_empty_query_set()
        def get_empty_query_set(self):
            return models.query.EmptyQuerySet()
    setattr(Photo, 'sizes', property(lambda self: PhotoSizesManagerProxy()))

else:
    class PhotoSize(models.Model):
        photo = models.ForeignKey(Photo, related_name='sizes')
        size = models.CharField(max_length = 10, choices=[(v['label'], k) for k,v in FLICKR_PHOTO_SIZES.iteritems()] )
        width = models.PositiveIntegerField(null=True, blank=True)
        height = models.PositiveIntegerField(null=True, blank=True)
        source = models.URLField(null=True, blank=True)

        class Meta:
            unique_together = (('photo', 'size'),)

    for key,size in FLICKR_PHOTO_SIZES.items():
        label = size.get('label', None)
        setattr(Photo, label, property(lambda self, label=label: PhotoSize.objects.get_or_create(photo=self, size=label)[0]))


class PhotoSetManager(models.Manager):

    def visible(self, *args, **kwargs):
        return self.get_query_set().filter(show=True).filter(*args, **kwargs)

    def _add_photos(self, obj, photos):
        for photo in photos:
            try:
                flickr_photo = Photo.objects.get(flickr_id=photo.id)
                obj.photos.add(flickr_photo)
            except Exception as e:
                pass

    def _prepare_data(self, info, photos, flickr_user=None, exif=None, geo=None):
        photoset = bunchify(info)
        photos = bunchify(photos['photoset']['photo'])

        data = {  'flickr_id': photoset.id, 'server': photoset.server,
                  'secret': photoset.secret, 'farm': photoset.farm, 'primary': photoset.primary,
                  'title': photoset.title._content, 'description': photoset.description._content,
                  'date_posted': ts_to_dt(photoset.date_create), 'date_updated': ts_to_dt(photoset.date_update),
                  'photos': photos,
                  'last_sync' : now(),
                  }
        if flickr_user:
            data['user'] = flickr_user
        return data

    def update_from_json(self, flickr_id, info, photos, update_photos=False, **kwargs):
        """Update a record with flickr_id"""
        photoset_data = self._prepare_data(info=info, photos=photos, **kwargs)
        photos = photoset_data.pop('photos')
        result = self.filter(flickr_id=flickr_id).update(**dict(photoset_data.items() + kwargs.items()))
        if result==1 and update_photos:
            obj = self.get(flickr_id=flickr_id)
            obj.photos.clear()
            self._add_photos(obj, photos)
        return result

    def create_from_json(self, flickr_user, info, photos, **kwargs):
        """Create a record for flickr_user"""
        photoset_data = self._prepare_data(flickr_user=flickr_user, info=info, photos=photos, **kwargs)
        photos = photoset_data.pop('photos')
        obj = self.create(**dict(photoset_data.items() + kwargs.items()))
        self._add_photos(obj, photos)
        return obj



class PhotoSet(FlickrModel):
    """http://www.flickr.com/services/api/explore/flickr.photosets.getInfo"""

    server = models.PositiveSmallIntegerField()
    farm = models.PositiveSmallIntegerField()
    secret = models.CharField(max_length=10)

    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    primary = models.CharField(max_length=50, null=True, blank=True) #flickr id of primary photo

    date_posted = models.DateTimeField(null=True, blank=True)
    date_updated = models.DateTimeField(null=True, blank=True)

    photos = models.ManyToManyField(Photo, null=True, blank=True)

    objects = PhotoSetManager()

    class Meta:
        ordering = ('-date_posted', '-id',)
        get_latest_by = 'date_posted'

    def __unicode__(self):
        return u'%s' % self.title

    def get_absolute_url(self):
        return reverse('flickr_photoset', args=[self.flickr_id,])

    def cover(self):
        try:
            return Photo.objects.get(flickr_id=self.primary)
        except Photo.DoesNotExist:
            try:
                return Photo.objects.filter(photoset__id__in=[self.id,]).latest()
            except Photo.DoesNotExist:
                pass


class JsonCache(models.Model):

    flickr_id = models.CharField(max_length=50, null=True, blank=True)
    info = models.TextField(null=True, blank=True)
    sizes = models.TextField(null=True, blank=True)
    exif = models.TextField(null=True, blank=True)
    geo = models.TextField(null=True, blank=True)
    exception = models.TextField(null=True, blank=True)
    added = models.DateTimeField(auto_now=True, auto_now_add=True)


