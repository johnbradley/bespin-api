"""
Handles communication with lando server that spawns VMs and runs jobs.
"""
from models import Job, LandoConnection
from lando_messaging.clients import LandoClient
from rest_framework.exceptions import ValidationError


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
    def __init__(self, job_id):
        """
        :param: job_id: int: id of the job we want to start/cancel/etc.
        """
        self.job_id = job_id
        self.config = LandoConfig()

    def start(self):
        """
        Place message in lando's queue to start running a job.
        The job must be at the NEW state or this will raise ValidationError.
        """
        job = self.get_job()
        if job.state == Job.JOB_STATE_NEW:
            self._make_client().start_job(self.job_id)
        else:
            raise ValidationError("Job is not at NEW state. Current state: {}.".format(job.get_state_display()))

    def _make_client(self):
        return LandoClient(self.config, self.config.work_queue_config.queue_name)

    def cancel(self):
        """
        Place message in lando's queue to cancel running a job.
        """
        job = self.get_job()  # make sure the job exists
        self._make_client().cancel_job(self.job_id)

    def get_job(self):
        return Job.objects.get(pk=self.job_id)
