from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        context['activate_url'] = 'https://supplyr.tk/'+context['key']
        return super().send_mail(template_prefix, email, context)