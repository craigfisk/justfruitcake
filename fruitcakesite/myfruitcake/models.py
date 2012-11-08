from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
#from django.db.models.signals import post_save

class Fruitcake(models.Model):
    thumbnail = models.ImageField("Thumbnail Pic", upload_to='thumbnails', blank=False, null=False)
    pic = models.ImageField("Regular Pic", upload_to='pics', blank=False, null=False)
    source = models.URLField(max_length=200, blank=True, null=True)
    #CF20121107: use quotes around Shipment and Upload in next 2 lines because classes not defined until below
    shipments = models.ManyToManyField('Shipment', related_name='shipments',verbose_name='shipments')
    uploads = models.ManyToManyField('Upload', related_name='uploads', verbose_name='uploads')

    def __unicode__(self):
        return unicode(self.thumbnail)

    #CF20121107  todo; compare forum.Post.profile_data()
    """
    def fruitcake_data(self): 
        uploads = self.uploads.upload_set.count()
        shipments = self.shipments.shipment_set.count()
        return uploads, shipments
    """

class Upload(models.Model):
    dt = models.DateTimeField(auto_now_add=True)
    fruitcake = models.ForeignKey(Fruitcake)
    uploader = models.OneToOneField(User)

    def __unicode__(self):
        return unicode(self.dt)

class Shipment(models.Model):
    dt = models.DateTimeField(auto_now_add=True) 
    fruitcake = models.ForeignKey(Fruitcake)
    sender = models.ForeignKey(User, verbose_name='senders', related_name='senders')
    receiver = models.ManyToManyField(User, verbose_name='addressees', related_name='receivers')

    def __unicode__(self):
        return unicode(self.dt)

### Admin
class FruitcakeAdmin(admin.ModelAdmin):
    list_display = ['thumbnail']

class UploadAdmin(admin.ModelAdmin):
    pass

class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['dt', 'fruitcake', 'sender', 'receiver']
