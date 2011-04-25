import re

from django import forms
from django.conf import settings

from amazon_resources.libs.amazon import AmazonAPI, asin_from_url


class ResourceForm(forms.Form):
    url = forms.CharField(max_length=255, help_text='URL of Amazon product')
    
    def __init__(self, *args, **kwargs):
        super(ResourceForm, self).__init__(*args, **kwargs)
        self.amazon = AmazonAPI(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    
    def clean_url(self):
        url = self.cleaned_data.get('url')
        if asin_from_url(url):
            return url
        else:
            raise forms.ValidationError('Could not determine ASIN from url')
    
    def clean(self):
        asin = asin_from_url(self.cleaned_data['url'])
        
        try:
            self.cleaned_data['resource'] = self.amazon.item_lookup(asin)
        except:
            exc_class, exc, tb = sys.exc_info()
            raise forms.ValidationError('Error looking up item, "%s"' % exc)
        
        return self.cleaned_data
