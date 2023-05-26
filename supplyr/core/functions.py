from django.db.models import Q
from supplyr.profiles.models import ManuallyCreatedBuyer, SalespersonPreregisteredUser
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib.staticfiles import finders
import os
from django.conf import settings


def check_and_link_manually_created_profiles(user):
    if manual_buyer := ManuallyCreatedBuyer.objects.filter(Q(mobile_number=user.mobile_number) | Q(email=user.email)).first():
        manual_buyer.buyer_profile.owner = user
        manual_buyer.buyer_profile.save()
        manual_buyer.is_settled = True
        manual_buyer.save()

    if preregistered_user := SalespersonPreregisteredUser.objects.filter(email = user.email).first():
        preregistered_user.salesperson_profile.owner = user
        preregistered_user.salesperson_profile.save()
        preregistered_user.is_settled = True
        preregistered_user.save()
        
def link_callback(uri, rel):
            """
            Convert HTML URIs to absolute system paths so xhtml2pdf can access those
            resources
            """
            result = finders.find(uri)
            if result:
                    if not isinstance(result, (list, tuple)):
                            result = [result]
                    result = list(os.path.realpath(path) for path in result)
                    path=result[0]
            else:
                    sUrl = settings.STATIC_URL        # Typically /static/
                    sRoot = settings.STATIC_ROOT      # Typically /home/userX/project_static/
                    mUrl = settings.MEDIA_URL         # Typically /media/
                    mRoot = settings.MEDIA_ROOT       # Typically /home/userX/project_static/media/

                    if uri.startswith(mUrl):
                            path = os.path.join(mRoot, uri.replace(mUrl, ""))
                    elif uri.startswith(sUrl):
                            path = os.path.join(sRoot, uri.replace(sUrl, ""))
                    else:
                            return uri

            # make sure that file exists
            if not os.path.isfile(path):
                    raise Exception(
                            'media URI must start with %s or %s' % (sUrl, mUrl)
                    )
            return path

def render_to_pdf(template_src, context_dict={}):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_src)
    html = template.render(context_dict)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response, link_callback=link_callback)
    # if error then show some funny view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response



