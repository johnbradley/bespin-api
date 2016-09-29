from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class DDSApplicationCredential(models.Model):
    """
    Stores the agent key for this application
    """
    name = models.CharField(max_length=255, blank=False, unique=True)
    agent_key = models.CharField(max_length=32, blank=False, unique=True)


class DDSUserCredential(models.Model):
    """
    DDS Credentials for bespin users
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=False)
    token = models.CharField(max_length=32, blank=False, unique=True)


class DDSResource(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=False)
    project_id = models.UUIDField(blank=False)
    path = models.TextField(null=False)

    class Meta:
        unique_together = (
            ('owner', 'project_id', 'path'),
        )

