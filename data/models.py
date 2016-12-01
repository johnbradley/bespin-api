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
    api_root = models.URLField()


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


class Workflow(models.Model):
    """
    Name of a workflow that will apply some processing to some data.
    """
    name = models.CharField(max_length=255, blank=False)

    def __unicode__(self):
        return self.name


class WorkflowVersion(models.Model):
    """
    Specific version of a Workflow.
    """
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='versions')
    object_name = models.CharField(max_length=255, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    version = models.CharField(max_length=32, blank=False)
    url = models.URLField()

    def __unicode__(self):
        return '{} version: {} created: {}'.format(self.workflow.name, self.version, self.created)


class Job(models.Model):
    """
    Instance of a workflow that is in some state of progress.
    """
    JOB_STATES = (
        ('N', 'New'),
        ('V', 'Create VM'),
        ('S', 'Staging In'),
        ('R', 'Running'),
        ('O', 'Store Job Output'),
        ('T', 'Terminate VM'),
        ('F', 'Finished'),
        ('E', 'Errored'),
        ('C', 'Canceled')
    )
    workflow_version = models.ForeignKey(WorkflowVersion, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    state = models.CharField(max_length=1, choices=JOB_STATES, default='N')
    last_updated = models.DateTimeField(auto_now=True, blank=False)
    vm_flavor = models.CharField(max_length=255, blank=False, default='m1.small')
    vm_instance_name = models.CharField(max_length=255, blank=False, null=True)

    def __unicode__(self):
        workflow_name = self.workflow_version.workflow
        return '{} state: {}'.format(workflow_name, self.get_state_display())


class JobParam(models.Model):
    STAGING_TYPE = (
        ('I', 'Input'),
        ('P', 'Param'),
        ('O', 'Output'),
    )
    JOB_FIELD_TYPES = (
        ('string', 'String'),
        ('integer', 'Integer'),
        ('dds_file', 'Duke DS File'),
        ('dds_file_array', 'Duke DS File Array'),
        ('url_file', 'File URL'),
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=False, related_name='params')
    staging = models.CharField(max_length=1, choices=STAGING_TYPE)
    name = models.CharField(max_length=255, blank=False)
    type = models.CharField(max_length=255, choices=JOB_FIELD_TYPES)
    value = models.CharField(max_length=255, null=True)

    def __unicode__(self):
        return 'Job {} - {} - {} - {}'.format(self.job.id, self.name, self.get_staging_display(),
                                                          self.get_type_display())


class JobParamDDSFile(models.Model):
    job_param = models.OneToOneField(JobParam, on_delete=models.CASCADE, null=False, related_name='dds_file')
    project_id = models.CharField(max_length=255, blank=False, null=True)
    file_id = models.CharField(max_length=255, blank=False, null=True)
    path = models.TextField(null=True)
    dds_app_credentials = models.ForeignKey(DDSApplicationCredential, on_delete=models.CASCADE)
    dds_user_credentials = models.ForeignKey(DDSUserCredential, on_delete=models.CASCADE)

