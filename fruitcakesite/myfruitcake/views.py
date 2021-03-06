import logging
logger = logging.getLogger(__name__)
from fruitcakesite.settings import FUNCTION_LOGGING
from django.contrib.auth.models import User
from lazysignup.templatetags.lazysignup_tags import is_lazy_user

from django.core.urlresolvers import reverse

from smtplib import SMTPException
from django.core.exceptions import ValidationError
from django.core.validators import validate_email#from string import join
#from PIL import Image as PImage
from os.path import join as pjoin

from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
#from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.core.context_processors import csrf
#from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.forms import ModelForm
#from django.contrib.auth.models import User
from fruitcakesite.settings import MEDIA_URL, CF_HOME_IP  #MEDIA_ROOT, WIDTH_AVATAR, WIDTH_THUMBNAIL

from myfruitcake.models import Fruitcake, Shipment, Like, IPAddress, FruitcakeException #Upload
from forum.models import UserProfile
from forum.views import mk_paginator #, profilepic  #userinfo

from django.views.generic import ListView, DetailView #, TemplateView, FormView  #DetailView

from django import forms

#from django.db import models

#from fruitcakesite.settings import DEFAULT_FROM_EMAIL
#from django.core.mail import EmailMessage # 
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context

#from datetime import datetime
from django.utils import timezone
from django.contrib.gis.geoip import GeoIP
import re
from lazysignup.decorators import allow_lazy_user   # replaces login_required() below and in myfruitcake.urls

#CF20130413 next line to enable THUMBNAIL_PATH etc to be a constant in templates. Leaving here as example.
#from django.conf import settings    # also needs render_to_response imported above

g = GeoIP()

"""
def testloggingviews():
    logger.debug("Testlogging in myfruitcake.views")
"""
"""
def testmap(request):
    return render_to_response("myfruitcake/map.html", add_csrf(request), context_instance=RequestContext(request))
"""

def about(request):
    return render_to_response("myfruitcake/about.html", add_csrf(request), context_instance=RequestContext(request))


def termsofservice(request):
    return render_to_response("myfruitcake/termsofservice.html", add_csrf(request), context_instance=RequestContext(request))


class ProfileForm(ModelForm):
    class Meta:
        model = UserProfile
#        exclude = ["posts", "user"]

"""
def activity(request, pk):
    #Listing of posts in a thread.
    shipments = Shipment.objects.all().order_by("dt")
    shipments = mk_paginator(request, shipments, 15)
    #CF20130413 added:
    #context['thumbnail_path'] = settings.THUMBNAIL_PATH
    return render_to_response("myfruitcake/activity.html", add_csrf(request, shipments=shipments, media_url=MEDIA_URL), context_instance=RequestContext(request))
"""

class FruitcakeListView(ListView):
    """For home page 
    """
#    @method_decorator(login_required)
#    def dispatch(self, *args, **kwargs):
#        return super(FruitcakeListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(FruitcakeListView, self).get_context_data(**kwargs)
        #context['user'] = self.request.user
        return context

    def get_queryset(self):

        return Fruitcake.objects.all().order_by('-times_shipped')[:10]


class MyFruitcakeListView(ListView):
    """For MyFruitcake / fruitcake_list.html
    """
#    @method_decorator(login_required)
#    def dispatch(self, *args, **kwargs):
#        return super(MyFruitcakeListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MyFruitcakeListView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        context['uploader'] = self.request.user
        
        context['upload'] = False
        path = self.request.get_full_path()
        pattern = '/myfruitcake/myfruitcake/$'
        m = re.match(pattern, path)
        if m: 
            context['upload'] = True

        return context

    def get_queryset(self):
        if self.request.user.id:   # should be is_authenticated not id
            return Fruitcake.objects.filter(uploader=self.request.user).order_by('-dt')
            # or: popup__startswith='Pick me'
        else:
            return Fruitcake.objects.all().order_by('-dt')


class MyFruitcakeDetailView(DetailView):

    model = Fruitcake

    def dispatch(self, *args, **kwargs):
        return super(MyFruitcakeDetailView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MyFruitcakeDetailView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        context['uploader'] = self.request.user
        return context
    """
    def get_queryset(self):
        self.fruitcake = get_object_or_404(Shipment, id=self.kwargs['pk'])  #self.kwargs['pk']
        #shipment = Shipment.objects.filter(origin_id=self.shipment.origin_id).order_by('-dt')
        return self.fruitcake
    """
  
class ShipmentListView(ListView):       
    """Template is shipment_list.html
    """

    def get_context_data(self, **kwargs):
        context = super(ShipmentListView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

    def get_queryset(self):
        # chain = Shipment.objects.filter(id__in=mylist)
        if self.request.user:
            s = Shipment.objects.filter(sender_id=self.request.user.id).order_by('-dt')
            return s
        

class ShipmentDetailView(DetailView):       
    """Template is shipment_detail.html
    """
    model = Shipment
    template_name = 'myfruitcake/shipment_detail.html'
     
    def get_context_data(self, **kwargs):
        context = super(ShipmentDetailView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

    def get_queryset(self):
        self.shipment = get_object_or_404(Shipment, id=self.kwargs['pk'])  #self.kwargs['pk']
        shipment = Shipment.objects.filter(origin_id=self.shipment.origin_id).order_by('-dt')
        #shipment = Shipment.objects.filter(sender=self.request.user).filter(origin_id=self.shipment.origin_id).order_by('-dt')

        return shipment

     
# https://docs.djangoproject.com/en/1.4/topics/forms/modelforms/   
# --> should read the modelforms doc from time to time.  For example: 
# "A subclass of ModelForm can accept an existing model instance as the keyword argument instance; if this is supplied,
# save() will update that instance. If it's not supplied, save() will create a new instance of the specified model"
# --> Especially, read the section "This save() method accepts an optional commit keyword argument, which  ..."

class ShipmentForm(ModelForm):
    class Meta:
        model = Shipment
        exclude = ('text',)

    def __init__(self, *args, **kwargs):
        super(ShipmentForm, self).__init__(*args, **kwargs)
        self.fields['sender'].widget = forms.TextInput()
        self.fields['receiver'].widget = forms.TextInput()
        
class MultiEmailField(forms.Field):
    def to_python(self, value):
        #Normalize to list of strings; return empty list if no input.
        if not value:
            return []
        # Create a list on any of pattern, strip white space, lowercase.
        pattern = '[;: ,]+'
        r = re.split(pattern, value.strip())
        return r
    # See https://docs.djangoproject.com/en/dev/ref/forms/validation/#form-field-default-cleaning
    def validate(self, value):
        #Check for valid email addresses
        if FUNCTION_LOGGING: logger.debug("Entering validate()")
        super(MultiEmailField, self).validate(value)
      
        for email in value:
            try:
                validate_email(email)
            except ValidationError as e:
                logger.debug("Email validation error on address '%s': %s" % (email, e))
                raise
                
class EmailContactForm(forms.Form):
    # see class MultiEmailField above
    email = MultiEmailField(help_text="(Please provide one or more email addresses.)", widget=forms.TextInput(attrs={'size':'32'}) )
    message = forms.CharField(max_length='256', widget=forms.Textarea(attrs={'size':'32'}) )
     
    #def check_addresses(self):
    #    for email in self.cleaned_data.get('emails'):
    #        email.validate(email)
    

from django.core.mail import get_connection
from django.forms.models import inlineformset_factory
from myfruitcake.models import EmailContact
from django.template import RequestContext


def increment_times_shipped(fruitcake_id):
    fruitcake = get_object_or_404(Fruitcake, pk=fruitcake_id)
    fruitcake.times_shipped += 1
    fruitcake.save()
        
class ShipmentError(Exception): pass


@allow_lazy_user
def email_fruitcake(request, fruitcake_id=None, shipment_id=None):
    """Create instance of Shipment and associated Addressees and send it as email. 
    Called with either a fruitcake_id or a shipment_id.
    Sender from request.user, plus a list of email addressees from the form.  
    Notes: 
    1) if fruitcake_id
    2) if shipment_id, create an instance of Shipment with m2m create of email addresses using the
    list, and then save all that,(see docs.djangoproject.com "Related Objects Reference") 
    3) email using EmailMultiAlternatives.

    The form is class EmailContactForm, which subclasses forms.Form and adds a MultiEmailField for the email 
    address[es] field  and puts a CharField Textarea form widget on the message field.

    Note: the form first applies is_valid() and then cleaned_data() to the form data.
    - form.is_valid() [from BaseForm] means not bool(self.errors) [and that binds the data to the form]
    """
    if FUNCTION_LOGGING: logger.debug("Entering validate()")
 
    sender_message = None
    #if request.method == 'POST':
    if request.method == 'POST' and request.user.is_authenticated():
        try:
            form = EmailContactForm(request.POST)
        except ValidationError as e:
            logger.debug("Email validation error on form: %s" % (e))
            raise

        try:
            form.is_valid()
            cd = form.cleaned_data # cd['email'] will now be the list of email addresses to send to
            message = cd['message']
            
            if (not fruitcake_id) and shipment_id: 
                s = get_object_or_404(Shipment, pk=shipment_id)
                fruitcake = Fruitcake.objects.get(pk=s.fruitcake_id)
            elif (not fruitcake_id):
                raise ShipmentError("Null values for both shipment_id and fruitcake_id.")
            else:
                fruitcake = Fruitcake.objects.get(pk=fruitcake_id)
           
            lazy = is_lazy_user(request.user)
            if hasattr(request.user, '_wrapped') and hasattr(request.user, '_setup'):
                if request.user._wrapped.__class__ == object:
                    request.user._setup()
                request.user = request.user._wrapped
           
            this_shipment, created = Shipment.objects.get_or_create(dt=timezone.now(),fruitcake=fruitcake,sender=request.user,message=message)
            #this_shipment = Shipment(dt=timezone.now(),fruitcake=fruitcake,sender=request.user, message=message)
            #this_shipment.save()

            if not shipment_id:
                this_shipment.origin = this_shipment
                this_shipment.parent = this_shipment
            else:
                prior_shipment = Shipment.objects.get(id=shipment_id)
                this_shipment.origin = prior_shipment.origin
                this_shipment.parent = prior_shipment
            
            #this_shipment.save()
            
            userprofile = UserProfile.objects.get(pk=request.user.id)
            userprofile.shipments += 1  #+= len(cd['email']) to increment number shipped to
            userprofile.save()
                  
            addr=request.META['REMOTE_ADDR']
            if (addr == '127.0.0.1' or addr == '192.168.1.100'):
                addr = CF_HOME_IP
            city=g.city(addr)

            # get_or_create() to only add unique ipaddressses. 
            # ip is the object; created is a boolean; true if new address, false if already created.

            ip, created = IPAddress.objects.get_or_create(ipaddress=addr,city=city['city'],region=city['region'],country_name=city['country_name'],country_code=city['country_code'])
            this_shipment.ipaddresses.add(ip)

            for email in cd['email']:
                # get_or_create() to only add unique email addresses to EmailContact that are not already there.
                # See https://docs.djangoproject.com/en/dev/ref/models/querysets/#django.db.models.query.QuerySet.get_or_create
                emailcontact, created = EmailContact.objects.get_or_create(email=email)
                this_shipment.emailcontacts.add(emailcontact)
               
            #Note: add an "emailed successfully" column to shipment (T/F) to set at the try below?

            # Notes: the emailing part --
            # https://docs.djangoproject.com/en/dev/topics/email/
            # CF20121126 solution: http://stackoverflow.com/questions/7583801/send-mass-emails-with-emailmultialternatives
            # CF20121129 on 1) mail test env and 2) connection management, see "SMTP Backend" and "Sending multiple emails" 
            """
            To retrieve gmail vs. other, go back to bbef9e1 Craig Fisk      Fri Dec 7 15:16:05 2012 -0800   "Got Home or MyFruitcake x Anonymous or SignedIn x
            display or click to send = all working again" -- this was an interim scheme to handle gmail separately.
            """
            ## x = [cd['email'].append(e) if e.split('@')[1] != 'gmail.com' else google.append(e) for e in cd['email'] ]
            # sections in https://docs.djangoproject.com/en/dev/topics/email/
            # CF20121129 on using Celery to send emails in the background, see documentation pointed to in
            # http://stackoverflow.com/questions/7626071/python-django-sending-emails-in-the-background

            connection = get_connection()  #uses smtp server specified in settings.py

            sender_message = cd['message']
            subject = 'Fruitcake for you!'
            
            if cd['email']:
                to = cd['email'].pop()
                if cd['email']:
                    bcc = cd['email']
                else:
                    bcc = None
                txty = get_template('myfruitcake/shipment_email.txt')
                htmly = get_template('myfruitcake/shipment_email.html')

                d = Context( {'fruitcake': fruitcake, 'shipment': this_shipment, 'sender_message': sender_message} )
                text_content = txty.render(d)
                html_content = htmly.render(d)
                msg = EmailMultiAlternatives(subject, text_content, from_email=request.user.email,to=(to,), bcc=bcc, connection=connection, headers={'Reply-To': request.user.email} )

                msg.attach_alternative(html_content, "text/html")

                try:
                    # If fail_silently=False, send_mail will raise an smtplib.SMTPException. See the smtplib docs for a list of
                    # possible exceptions, all of which are subclasses of SMTPException.
                    # see https://docs.djangoproject.com/en/1.4/topics/email/#email-backends
                    msg.send(fail_silently=False)
                except SMTPException as e:
                    logger.debug("SMTPException: %s, on shipment to: %s with bcc: %s, with message: %s" % (e, to, bcc, msg))
                    raise
                
            #if not this_shipment.origin:
            #    this_shipment_origin = 0
            #else:
            #    this_shipment_origin = this_shipment.origin
            #if not this_shipment.parent:
            #    this_shipment_parent = 0
            #else:
            #    this_shipment_parent = this_shipment.parent
            this_shipment.save()
            return HttpResponseRedirect(reverse('fruitcake:shipments') )
        
        except Exception as e:
            logger.debug("Sorry, while trying to ship, got Exception: %s" % (e))
            #raise

    #CF20121217 to require login for sending if not is_authenticated
    elif request.method == 'POST':
        return HttpResponseRedirect('/login/?next=%s' % request.path)

    else:
        if sender_message:
            message = sender_message
        else:
            message = 'Fruitcake for you!'

        form = EmailContactForm(initial={'message': message})

    if fruitcake_id:
        fruitcake = Fruitcake.objects.get(id=fruitcake_id)
    else:
        fruitcake=None
    if shipment_id:
        shipment = Shipment.objects.get(id=shipment_id)
    else:
        shipment=None
                
    return render_to_response('myfruitcake/fruitcake_shipment.html', add_csrf(request, form=form, fruitcake=fruitcake,shipment=shipment), context_instance=RequestContext(request))

class UploadFruitcakeForm(ModelForm):
    class Meta:
        model = Fruitcake
        exclude = ['uploader', 'shipments', 'uploads', 'source', 'times_shipped']

class LikeForm(ModelForm):
    class Meta:
        model = Like
        exclude = ['dt', 'fruitcake', 'user'] 

@allow_lazy_user
def upload_file(request):

    if FUNCTION_LOGGING: logger.debug("Entering upload_file()")

    if request.method == "POST":

        form = UploadFruitcakeForm(request.POST, request.FILES)
        
        # See if there already is an upload of this file for this user
        prior_fruitcake = Fruitcake.objects.filter(uploader=request.user)
        pattern = re.compile('^pics\/')
        prior_files = []
        x = [ prior_files.append(pattern.sub('', str(f.pic.name))) for f in prior_fruitcake ] 

        previously_uploaded = request.FILES['pic'].name in prior_files
        #if form.is_valid() and not previously_uploaded:
        if form.is_valid():
            if not previously_uploaded:
                pic = form.save(commit=False)
                # then add the request.user
                pic.uploader = request.user

                file_to_upload = str(request.FILES['pic'])
                pic.pic.name = pjoin('pics/', file_to_upload)
                pic.thumbnail.name = pjoin('thumbnails/', file_to_upload)

                # .save() method on the model saves 2 processed versions of the image in pics and thumbnails
                pic.save()
                return HttpResponseRedirect(reverse('fruitcake:listview') )  
            else:
                return HttpResponse('Oops! You already uploaded this file. Please try a different one. Thanks!')

    else:
        form = UploadFruitcakeForm()

    return render_to_response('myfruitcake/fruitcake_upload.html', add_csrf(request, form=form), context_instance=RequestContext(request)) 

"""
def duplicate(request):
    return HttpResponse("Duplicate; please try again!")
"""

def add_csrf(request, **kwargs):
    d = dict(user=request.user, **kwargs)
    d.update(csrf(request))
    return d


@staff_member_required
def path(request):
    s= " request.path: %s<br />" % (request.path)
    s+= " request.get_full_path(): %s<br />" % (request.get_full_path() )
    s+= " request.get_host(): %s<br />" % (request.get_host() )
    s+= " request.is_secure(): %s<br />" % (request.is_secure() )
    return HttpResponse(s)

@staff_member_required
def meta(request):
    values = request.META.items()
    values.sort()
    html = []
    for k,v in values:
        html.append('<tr><td>%s</td></tr><tr><td>%s</td></tr>' % (k, v))
    return HttpResponse('<table>%s</table>' % '\n'.join(html))

"""
@staff_member_required
def search_form(request):
    return render_to_response('myfruitcake/search_form.html', {'user': request.user} , context_instance=RequestContext(request))
"""

@staff_member_required
def search(request):
    profile = UserProfile.objects.get(user=request.user)
    errors = []
    if 'q' in request.GET:
        q = request.GET['q']
        if not q:
            errors.append('Please enter a search term.')
        elif len(q) > 20:
            errors.append('Please enter at most 20 characters.')
        else:
            fruitcakes = Fruitcake.objects.filter(popup__icontains=q)
            if len(fruitcakes):
                return render_to_response('myfruitcake/search_results.html', {'fruitcakes': fruitcakes, 'query':q,
                    'user':request.user}, context_instance=RequestContext(request))
            else:
                errors.append('No results for that search.')

    return render_to_response('myfruitcake/search_form.html', {'errors': errors, 'user': request.user} , context_instance=RequestContext(request))



