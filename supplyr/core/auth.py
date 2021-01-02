from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings

class CustomAccountAdapter(DefaultAccountAdapter):

    def send_mail(self, template_prefix, email, context):
        context['activate_url'] = settings.URL_FRONTEND + 'confirm-email/' + context['key']
        return super().send_mail(template_prefix, email, context)