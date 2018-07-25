from data.models import Job, JobDDSOutputProject, DDSJobInputFile, DDSUserCredential
from exceptions import JobFactoryException
import json
import math

BYTES_TO_GB_DIVISOR = 1024 * 1024 * 1024


def create_job_factory(job_answer_set):
    """
    Create JobFactory based on questions and answers referenced by job_answer_set.
    :param user: User: user who's credentials we will use for building the job
    :param job_answer_set: JobAnswerSet: references questions and their answers to use for building a Job.
    :return: JobFactory
    """
    user = job_answer_set.user
    vm_settings = job_answer_set.questionnaire.vm_settings
    workflow_version = job_answer_set.questionnaire.workflow_version
    stage_group = job_answer_set.stage_group
    user_job_order_dict = json.loads(job_answer_set.user_job_order_json)
    system_job_order_dict = json.loads(job_answer_set.questionnaire.system_job_order_json)
    job_name = job_answer_set.job_name
    vm_flavor = job_answer_set.questionnaire.vm_flavor
    volume_size = calculate_volume_size(job_answer_set)
    volume_mounts = job_answer_set.questionnaire.volume_mounts
    share_group = job_answer_set.questionnaire.share_group
    fund_code = job_answer_set.fund_code
    factory = JobFactory(user, workflow_version, stage_group, user_job_order_dict, system_job_order_dict, job_name,
                         vm_settings, vm_flavor, volume_size, volume_mounts, share_group, fund_code)

    return factory


def calculate_volume_size(job_answer_set):
    """
    Calculates the volume size needed based on the job_answer_set questionnaire settings and stage group data.
    :param job_answer_set: JobAnswerSet: contains questionnaire and stage_group used in calculation
    :return: int: size in GB: volume_size_factor * data_size_in_gb + volume_size_base
    """
    base_in_gb = job_answer_set.questionnaire.volume_size_base
    factor = job_answer_set.questionnaire.volume_size_factor
    data_size_in_gb = calculate_stage_group_size(job_answer_set.stage_group)
    return int(math.ceil(base_in_gb + float(factor) * data_size_in_gb))


def calculate_stage_group_size(stage_group):
    """
    Total up the size of the files contained in the passed stage_group
    :param stage_group: JobFileStageGroup that may contain dds_files and/or url_file
    :return: float: size in GB of all files in the stage group
    """
    total_size_in_bytes = 0
    for dds_file in stage_group.dds_files.all():
        total_size_in_bytes += dds_file.size
    for url_file in stage_group.url_files.all():
        total_size_in_bytes += url_file.size
    return float(total_size_in_bytes) / BYTES_TO_GB_DIVISOR


class JobFactory(object):
    """
    Creates Job record in the database based on questions their answers.
    """
    def __init__(self, user, workflow_version, stage_group, user_job_order, system_job_order, job_name, vm_settings,
                 vm_flavor, volume_size, volume_mounts, share_group, fund_code):
        """
        Setup factory
        :param user: User: user we are creating this job for and who's credentials we will use
        :param workflow_version: WorkflowVersion: which CWL workflow are we building a job for
        """
        self.workflow_version = workflow_version
        self.user = user
        self.stage_group = stage_group
        self.user_job_order = user_job_order
        self.system_job_order = system_job_order
        self.job_name = job_name
        self.vm_settings = vm_settings
        self.vm_flavor = vm_flavor
        self.volume_size = volume_size
        self.volume_mounts = volume_mounts
        self.share_group = share_group
        self.fund_code = fund_code

    def create_job(self, is_authorized):
        """
        Create a job based on the workflow_version, system job order and user job order
        :param is_authorized: bool: if True job is created in authorized state
        :return: Job: job that was inserted into the database along with it's output project and input files.
        """
        if self.system_job_order is None or self.user_job_order is None:
            raise JobFactoryException('Attempted to create a job without specifying system job order or user job order')

        # Create the job order to be submitted. Begin with the system info and overlay the user order
        job_order = self.system_job_order.copy()
        job_order.update(self.user_job_order)

        job_state = Job.JOB_STATE_NEW
        if is_authorized:
            job_state = Job.JOB_STATE_AUTHORIZED
        job = Job.objects.create(workflow_version=self.workflow_version,
                                 user=self.user,
                                 stage_group=self.stage_group,
                                 name=self.job_name,
                                 vm_settings=self.vm_settings,
                                 job_order=json.dumps(job_order),
                                 volume_size=self.volume_size,
                                 vm_volume_mounts=self.volume_mounts,
                                 vm_flavor=self.vm_flavor,
                                 share_group=self.share_group,
                                 fund_code=self.fund_code,
                                 state=job_state
        )
        # Create output project
        # just taking the first worker user credential for now(there is only one production DukeDS instance)
        worker_user_credentials = DDSUserCredential.objects.first()
        JobDDSOutputProject.objects.create(job=job, dds_user_credentials=worker_user_credentials)
        return job

