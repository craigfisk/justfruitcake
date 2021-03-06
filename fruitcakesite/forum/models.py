import logging
logger = logging.getLogger(__name__)
from fruitcakesite.settings import FUNCTION_LOGGING

from django.db import models
from django.contrib.auth.models import User
#from django.contrib import admin
from django.db.models.signals import post_save
from django.utils.timezone import localtime
from django.utils.formats import localize

class Forum(models.Model):
    title = models.CharField(max_length=60)

    def __unicode__(self):
        return self.title

    def num_posts(self):
        return sum([t.num_posts() for t in self.thread_set.all()])

    def last_post(self):
        if self.thread_set.count():
            last = None
            for t in self.thread_set.all():
                l = t.last_post()
                if l:
                    if not last or l.created > last.created:
                        last = l
            return last


class Thread(models.Model):
    title = models.CharField(max_length=60)
    created = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User, blank=True, null=True)
    forum = models.ForeignKey(Forum)

    def __unicode__(self):
        return unicode(self.creator) + " - " + self.title

    def num_posts(self):
        return self.post_set.count()

    def num_replies(self):
        return self.post_set.count() - 1

    def last_post(self):
        if self.post_set.count():
            return self.post_set.order_by("created")[0]


class Post(models.Model):
    title = models.CharField(max_length=60)
    created = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User, blank=True, null=True)
    thread = models.ForeignKey(Thread)
    body = models.TextField(max_length=10000)

    def __unicode__(self):
        return u"%s - %s - %s" % (self.creator, self.thread, self.title)

    def short(self):
        #return u"%s - %s\n%s" % (self.creator, self.title, self.created.strftime("%b %d, %I:%M %p"))
        return u"%s - %s\n%s" % (self.creator, self.title, localize(localtime(self.created)) )
    short.allow_tags = True

    def profile_data(self):
        #CF20121105 modified following
#        p = self.creator.userprofile_set.all()[0]
#        return p.posts, p.avatar
        posts = self.creator.post_set.count()
        avatar = self.creator.userprofile.avatar
        return posts, avatar

class UserProfile(models.Model):
    # was upload_to="images/" in Django by Example but ReadTheDocs "How do I use image and file fields" says MEDIA_ROOT
    # See http://readthedocs.org/docs/django/en/latest/faq/usage.html#how-do-i-use-image-and-file-fields
    # See also forum/views.py
    if FUNCTION_LOGGING:  logger.debug("Entering class UserProfile")
    avatar = models.ImageField("Profile photo", upload_to='images', blank=True, null=True)
    posts = models.IntegerField(default=0)
    shipments = models.IntegerField(default=0)
    user = models.OneToOneField(User)

    def __unicode__(self):
        return unicode(self.user)

    def date_joined(self):
        return self.user.date_joined

####CF20121105 replacing following function (and UserProfile.user def above) on model of 1.4 django docs
# see https://docs.djangoproject.com/en/1.4/topics/auth/#storing-additional-information-about-users
# instead of the Django by Example code --> mostly motivated by getting user.get_profile.avatar access
# in userinfo block in templates.
"""
def create_user_profile(sender, **kwargs):
    #When creating a new user, make a profile for him.
    u = kwargs["instance"]
    if not UserProfile.objects.filter(user=u):
        UserProfile(user=u).save()
"""
def create_user_profile(sender, instance, created, **kwargs):
    if FUNCTION_LOGGING:  logger.debug("Entering create_user_profile()")
        
    if created:
        UserProfile.objects.create(user=instance)


post_save.connect(create_user_profile, sender=User)

