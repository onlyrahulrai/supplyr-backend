from django.db.models import fields
import django_filters
from supplyr.profiles.models import SellerProfile
from django_filters import CharFilter

class SellerProfileFilter(django_filters.FilterSet):
    search = CharFilter(field_name="business_name",lookup_expr="icontains")
    class Meta:
        model = SellerProfile
        fields = ["search","entity_category","entity_type","is_gst_enrolled","is_active","status"]
        
    def __init__(self, *args,**kwargs):
        super(SellerProfileFilter,self).__init__(*args,**kwargs)
        self.filters["search"].label=""
        self.filters["is_gst_enrolled"].label="GST Enrolled"
        self.filters["is_active"].label="Active"
        self.form.fields['search'].widget.attrs = {'placeholder':'Type Business name...'} 
        
    