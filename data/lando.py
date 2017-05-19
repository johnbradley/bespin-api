"""
Handles communication with lando server that spawns VMs and runs jobs.
Also updates job state before sending messages to lando.
"""
from models import Job, LandoConnection
from lando_messaging.clients import LandoClient
from rest_framework.exceptions import ValidationError
from util import give_download_permissions


class LandoConfig(object):
    """
    Settings for the AMQP queue we send messages to lando server over.
    """
    def __init__(self):
        self.work_queue_config = LandoConnection.objects.first()


class LandoJob(object):
    """
    Sends messages to lando based on a job.
    """
    def __init__(self, job_id, user):
        """
        :param: job_id: int: id of the job we want to start/cancel/etc.
        :param: user: Django User: user who provides DukeDS permissions for start/restart
        """
        self.job_id = job_id
        self.user = user
        self.config = LandoConfig()

    def start(self):
        """
        Place message in lando's queue to start running a job.
        Sets job state to STARTING.
        The job must be at the NEW state or this will raise ValidationError.
        """
        job = self.get_job()
        if job.state == Job.JOB_STATE_NEW:
            job.state = Job.JOB_STATE_STARTING
            job.save()
            self._give_download_permissions(job)
            self._make_client().start_job(self.job_id)
        else:
            raise ValidationError("Job is not at NEW state. Current state: {}.".format(job.get_state_display()))

    def _make_client(self):
        return LandoClient(self.config, self.config.work_queue_config.queue_name)

    def cancel(self):
        """
        Place message in lando's queue to cancel running a job.
        Sets job state to CANCELING.
        """
        job = self.get_job()  # make sure the job exists
        job.state = Job.JOB_STATE_CANCELING
        job.save()
        self._make_client().cancel_job(self.job_id)

    def restart(self, user):
        """
        Place message in lando's queue to restart a job that had an error or was canceled.
        Sets job state to RESTARTING.
        The job must be at the ERROR or CANCEL state or this will raise ValidationError.
        """
        job = self.get_job()
        if job.state == Job.JOB_STATE_ERROR or job.state == Job.JOB_STATE_CANCEL:
            job.state = Job.JOB_STATE_RESTARTING
            job.save()
            self._give_download_permissions(job)
            self._make_client().restart_job(self.job_id)
        else:
            raise ValidationError("Job is not at ERROR or CANCEL state. Current state: {}.".format(job.get_state_display()))

    def get_job(self):
        return Job.objects.get(pk=self.job_id)

    def _give_download_permissions(self, job):
        """
        Give download permissions to the bespin user for the projects that contain input files. 
        :param job: Job: job containing files in one or more projects
        """
        unique_project_user_cred = set()
        for input_file in job.input_files.all():
            for dds_file in input_file.dds_files.all():
                unique_project_user_cred.add((dds_file.project_id, dds_file.dds_user_credentials))
        for project_id, dds_user_credential in unique_project_user_cred:
            give_download_permissions(self.user, project_id, dds_user_credential.dds_id)
