from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    
    @property
    def name(self):
        return self.first_name

    @name.setter
    def name(self, value):
        self.first_name = value
        self.save()

    @property
    def state(self):
        return 'registered'