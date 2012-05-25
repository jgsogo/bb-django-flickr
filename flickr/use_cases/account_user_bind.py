#!/usr/bin/env python
# encoding: utf-8

from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.functional import wraps
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

def on_class_prepared(sender, **kwargs):
    """
    class_prepared signal handler that checks for the model named
    MyModel as the sender, and adds a User fk to it.
    """
    if sender.__name__ == "FlickrAccount":
        user = models.OneToOneField(User)
        user.contribute_to_class(sender, 'user')
        User.flickr_account = property(lambda u: sender.objects.get_or_create(user=u)[0])


def flickr_oauth_view_decorator(view):
    @wraps(view)
    def inner(request, *args, **kwargs):
        user = request.user
        if user.flickr_account.token != '' and view.__name__ != 'oauth_validate':
            return HttpResponseRedirect(reverse('flickr_auth_validate', kwargs = {'nsid' : user.flickr_account.nsid}))
        return view(request, user=user, *args, **kwargs)
    return login_required(inner)


def flickr_sync_command_decorator(handle):
    from flickr.models import FlickrAccount
    @wraps(handle)
    def inner(*args, **kwargs):
        user_id = kwargs.get('user_id', None)
        add_accounts = kwargs.get('add_accounts', [])
        if user_id:
            add_accounts.extend(list(FlickrAccount.objects.filter(user__id=user_id)))
            kwargs.pop('account')
            kwargs.pop('nsid')
        return handle(add_accounts=add_accounts, *args, **kwargs)
    return inner
