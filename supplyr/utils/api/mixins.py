
class APISourceMixin():

    @property
    def api_source(self):
        return self.kwargs.get('api_source')