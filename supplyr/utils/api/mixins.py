from supplyr.profiles.serializers import UserDetailsSerializer
class APISourceMixin():

    @property
    def api_source(self):
        return self.kwargs.get('api_source')

class SerializerAPISourceMixin():

    @property
    def api_source(self):
        if 'request' in self.context:
            # requests will only be available is passed in extra context. dj-rest-auth passes in default views
            request = self.context['request']
            kwargs = request.resolver_match.kwargs
            if 'api_source' in kwargs:
                return kwargs['api_source']
        return None


class UserInfoMixin():

    # @staticmethod
    def get_user_info(self, user):
        extra_context = {}
        if hasattr(self, 'request'):
            extra_context['request'] = self.request

        serializer = UserDetailsSerializer(user, context=extra_context)
        return serializer.data

    def inject_user_info(self, data, user):
        user_info = self.get_user_info(user)
        _data = data # so that it may work if someone passes serializer.data, to which changes do not reflect wothout making a copy
        _data['user_info'] = user_info
        return _data
