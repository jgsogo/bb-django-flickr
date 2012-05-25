#!/usr/bin/env python
# encoding: utf-8

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import class_prepared

def add_field(sender, **kwargs):
    """
    class_prepared signal handler that checks for the model named
    MyModel as the sender, and adds a User fk to it.
    """
    if sender.__name__ == "FlickrAccount":
        user = models.OneToOneField(User)
        user.contribute_to_class(sender, 'user')

class_prepared.connect(add_field)

