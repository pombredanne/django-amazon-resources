import os
import urllib

from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from django.core.files import File
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.defaultfilters import slugify

from amazon_resources.forms import ResourceForm
from amazon_resources.libs.image_resize import resize
from amazon_resources.models import ResourceCategory, MediaType, Resource


THUMB_WIDTH = getattr(settings, 'THUMB_WIDTH', 200)
THUMB_HEIGHT = getattr(settings, 'THUMB_WIDTH', None)


class ResourceAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'title', 'author', 'category', 'recommended',)
    list_filter = ('category', 'media_type', 'recommended',)
    
    def get_urls(self):
        urlpatterns = super(ResourceAdmin, self).get_urls()
        custom_patterns = patterns('',
            url(r'^add/$', 
                self.admin_site.admin_view(self.add_view),
                name='admin_add_resource'),
        )
        return custom_patterns + urlpatterns
    
    def add_view(self, request):
        form = ResourceForm(request.POST or None)
        if request.method == 'POST':
            if form.is_valid():
                api_resource = form.cleaned_data['resource']
                
                media_type, _ = MediaType.objects.get_or_create(
                    title=api_resource['productgroup']
                )
                
                resource = Resource.objects.create(
                    asin=api_resource['asin'],
                    title=api_resource['title'],
                    author=api_resource['author'],
                    media_type=media_type,
                    pub_date=api_resource['publicationdate'],
                    pages=api_resource['numberofpages'] or 0,
                )
                
                img_url = api_resource['image']
                if img_url:
                    img_name, extension = img_url.rsplit('.', 1)
                    
                    # download the image and store it in memory
                    image_data, _ = urllib.urlretrieve(img_url)
                    
                    resource.cover_image.save(
                        '%s.%s' % (slugify(resource.title)[:30], extension),
                        File(open(image_data))
                    )
                    
                    # resize the newly created image
                    resize(
                        resource.cover_image.name,
                        resource.cover_image.name,
                        THUMB_WIDTH,
                        THUMB_HEIGHT
                    )
                    
                    resource.save()
                
                return HttpResponseRedirect(reverse("admin:amazon_resources_resource_change", args=[resource.pk]))
        
        return render_to_response('admin/amazon_resources/add_amazon_resource.html', {
            'title': 'Add a resource', 'form': form
        }, context_instance=RequestContext(request))


class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'sort_order')
    list_editable = ('sort_order',)


admin.site.register(Resource, ResourceAdmin)
admin.site.register(ResourceCategory, ResourceCategoryAdmin)
admin.site.register(MediaType)
