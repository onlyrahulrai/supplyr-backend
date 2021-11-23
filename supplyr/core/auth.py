from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
import threading

class CustomAccountAdapter(DefaultAccountAdapter):

    def send_mail(self, template_prefix, email, context):
        context['activate_url'] = settings.URL_FRONTEND + 'confirm-email/' + context['key']
        mailing_thread = threading.Thread(target=super(CustomAccountAdapter,self).send_mail,args=(template_prefix,email,context))
        mailing_thread.start()