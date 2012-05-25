#!/usr/bin/env python
# encoding: utf-8

"""
This file gathers all the stuff used in the application but depending
on the flickr service. Having it all together in one place will help
maintenance just in case flickr opts to change anything.

References:
 * http://www.flickr.com/help/photos/
 * http://www.flickr.com/services/api/misc.urls.html
"""

FLICKR_PHOTO_URL = 'http://farm%(farm-id)s.staticflickr.com/%(server-id)s/%(photo-id)s_%(secret)s%(size_suffix)s.%(format)s'
FLICKR_SHORT_PHOTO_URL = 'http://flic.kr/p/%(short-photo-id)s'
FLICKR_URL_PAGE = 'http://www.flickr.com/photos/%(user-id)s/%(photo-id)s/'
FLICKR_PHOTOS_URL = 'http://www.flickr.com/photos/%(user-id)s/'
FLICKR_PROFILE_URL = 'http://www.flickr.com/people/%(user-id)s/'
FLICKR_BUDDY_ICON = 'http://farm%(icon-farm)s.staticflickr.com/%(icon-server)s/buddyicons/%(nsid)s.jpg'
FLICKR_BUDDY_ICON_DEFAULT = 'http://www.flickr.com/images/buddyicon.gif'

""" Photo urls
"""

FLICKR_PHOTO_SIZES = {
    'Square' : {'label' : 'square',
                'width' : 75,
                'height' : 75,
                'suffix' : 's',
                },
    'Large Square' : {  'label' : 'largesquare',
                        'width' : 150,
                        'height' : 150,
                        'suffix' : 'q',
                        },
    'Thumbnail' : { 'label' : 'thumb',
                    'longest' : 100,
                    'suffix' : 't',
                },
    'Small' : { 'label' : 'small',
                'longest' : 240,
                'suffix' : 'm',
                },
    'Small 320' : { 'label' : 'small320',
                    'longest' : 320,
                    'suffix' : 'n',
                },
    'Medium' : {'label' : 'medium',
                'longest' : 500,
                },
    'Medium 640' : {'label' : 'medium640',
                    'longest' : 640,
                    'suffix' : 'z',
                },
    'Medium 800' : {'label' : 'medium800',
                    'longest' : 800,
                    'suffix' : 'c',
                },
    'Large' : { 'label' : 'large',
                'longest' : 1024,
                'suffix' : 'b',
                },
    'Original' : {  'label' : 'ori',
                    'suffix' : 'o',
                },
    }

def get_size_from_label(label):
    for key, size_item in FLICKR_PHOTO_SIZES.items():
        if label == size_item.get('label', None):
            return size_item

def build_photo_url(farm_id, server_id, photo_id, secret, size, format='jpg'):
    size_suffix = ''
    if size.get('suffix', False):
        size_suffix = '_%s' % size['suffix']
    return FLICKR_PHOTO_URL % {
                                'farm-id':farm_id,
                                'server-id':server_id,
                                'photo-id':photo_id,
                                'secret':secret,
                                'size_suffix':size_suffix,
                                'format':format,
                                }


""" base58
http://www.flickr.com/groups/api/discuss/72157616713786392/
"""
alphabet = '123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
base = len(alphabet)

def b58encode(div, s=''):
    if div >= base:
        div, mod = divmod(div, base)
        return b58encode(div, alphabet[mod] + s)
    return alphabet[div] + s

def b58decode(s):
    return sum(alphabet.index(c) * pow(base, i) for i, c in enumerate(reversed(s)))

