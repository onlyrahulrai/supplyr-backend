from django.db.models import fields
from django_filters import FilterSet, filters, widgets
from supplyr.profiles.models import SellerProfile
from django_filters import CharFilter




class SellerProfileFilter(FilterSet):
    '''
        This is a custom filter created with the django_filters package.It's created for filtering users from the Database by thier Status,Name,Business Name etc.
    '''
    search = CharFilter(field_name="business_name",lookup_expr="icontains")
    
    sort = filters.OrderingFilter(fields=['id',"business_name","owner","entity_category","entity_type","status","is_gst_enrolled","is_active"], widget=widgets.LinkWidget)

    class Meta:
        model = SellerProfile
        fields = ["search","entity_category","entity_type","is_gst_enrolled","is_active","status","sort"]
        ordering_fields = '__all__'
        
        
    def __init__(self, *args,**kwargs):
        super(SellerProfileFilter,self).__init__(*args,**kwargs)
        self.filters["search"].label=""
        self.filters["status"].label=""
        self.filters["is_gst_enrolled"].label="GST Enrolled"
        self.filters["is_active"].label="Active"
        self.form.fields['search'].widget.attrs = {'placeholder':'Type Business name...'} 
        
