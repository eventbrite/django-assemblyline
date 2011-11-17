# Necessary to get Django to automatically run the tests.
from django.db import models


class TestUser(models.Model):

    username = models.CharField(
        max_length=100,
        blank=False,
    )
    email = models.EmailField(blank=True)


class TestModel(models.Model):

    user = models.ForeignKey(TestUser)
    required = models.CharField(
        max_length=100,
        blank=False,
    )
    optional = models.CharField(
        max_length=100,
        blank=True,
    )
