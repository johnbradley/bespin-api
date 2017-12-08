from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError
from mock.mock import MagicMock, patch, Mock
from models import DDSEndpoint, DDSUserCredential, Workflow, WorkflowVersion, JobFileStageGroup, ShareGroup, \
    DDSJobInputFile, URLJobInputFile, VMFlavor, VMProject, VMSettings, CloudSettings
from jobfactory import JobFactory, JobFactoryException, calculate_stage_group_size, calculate_volume_size
import json


FLY_RNASEQ_URL = "https://raw.githubusercontent.com/Duke-GCB/bespin-cwl/master/packed-workflows/rnaseq-pt1-packed.cwl"


class JobFactoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test_user')
        self.endpoint = DDSEndpoint.objects.create(name='app1', agent_key='abc123')
        self.worker_cred = DDSUserCredential.objects.create(user=self.user, token='abc123', endpoint=self.endpoint)
        workflow = Workflow.objects.create(name='RnaSeq')
        self.workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                               object_name='#main',
                                                               version='1',
                                                               url=FLY_RNASEQ_URL)
        self.stage_group = JobFileStageGroup.objects.create(user=self.user)
        self.share_group = ShareGroup.objects.create(name='result data checkers')
        vm_project = VMProject.objects.create(name='project1')
        cloud_settings = CloudSettings.objects.create(name='cloud1', vm_project=vm_project)
        self.vm_settings = VMSettings.objects.create(name='settings1', cloud_settings=cloud_settings)
        self.vm_flavor = VMFlavor.objects.create(name='flavor1')

    # What does job factory do now?
    # Checks that orders are not none
    # merges dictionaries
    # Creates a job
    # Creates a job output project

    def test_requires_user_order(self):
        user_job_order = None
        system_job_order = {}
        job_factory = JobFactory(self.user, None, None, user_job_order, system_job_order, None, None, None, 150,
                                 self.share_group, '123-4')
        with self.assertRaises(JobFactoryException):
            job_factory.create_job()

    def test_requires_system_order(self):
        user_job_order = {}
        system_job_order = None
        job_factory = JobFactory(self.user, None, None, user_job_order, system_job_order, None, None, None, 150,
                                 self.share_group, '123-4')
        with self.assertRaises(JobFactoryException):
            job_factory.create_job()

    def test_creates_job(self):
        user_job_order = {'input1': 'user'}
        system_job_order = {'input2' : 'system'}
        job_factory = JobFactory(self.user, self.workflow_version, self.stage_group, user_job_order, system_job_order,
                                 'Test Job', self.vm_settings, self.vm_flavor, 110, self.share_group, '123-4')
        job = job_factory.create_job()
        self.assertEqual(job.user, self.user)
        self.assertEqual(job.workflow_version, self.workflow_version)
        expected_job_order = json.dumps({'input1':'user','input2':'system'})
        self.assertEqual(expected_job_order, job.job_order)
        self.assertEqual(job.name, 'Test Job')
        self.assertEqual(job.vm_settings, self.vm_settings)
        self.assertEqual(job.vm_flavor, self.vm_flavor)
        self.assertEqual(self.worker_cred.id, job.output_project.dds_user_credentials.id)
        self.assertEqual(job.volume_size, 110)
        self.assertEqual(job.share_group, self.share_group)
        self.assertEqual(job.fund_code, '123-4')

    def test_favors_user_inputs(self):
        user_job_order = {'input1': 'user'}
        system_job_order = {'input1' : 'system'}
        job_factory = JobFactory(self.user, self.workflow_version, self.stage_group, user_job_order, system_job_order,
                                 'Test Job', self.vm_settings, self.vm_flavor, 120, self.share_group, '123-4')
        job = job_factory.create_job()
        expected_job_order = json.dumps({'input1':'user'})
        self.assertEqual(expected_job_order, job.job_order)

    def test_calculate_stage_group_size(self):
        stage_group = JobFileStageGroup.objects.create(user=self.user)
        dds_file_sizes = [10 * 1024 * 1024,  # 10 MB
                          2.5 * 1024 * 1024 * 1024,  # 2.5 GB
                          ]
        url_file_sizes = [0.5 * 1024 * 1024 * 1024]  # 0.5 GB
        for size in dds_file_sizes:
            DDSJobInputFile.objects.create(stage_group=stage_group, dds_user_credentials=self.worker_cred, size=size)
        for size in url_file_sizes:
            URLJobInputFile.objects.create(stage_group=stage_group, size=size)
        self.assertEqual(3.00977, round(calculate_stage_group_size(stage_group), 5))

    @patch('data.jobfactory.calculate_stage_group_size')
    def test_calculate_volume_size(self, mock_calculate_stage_group_size):
        mock_calculate_stage_group_size.return_value = 20
        mock_vm_settings = Mock(volume_size_base=10, volume_size_factor=4)
        mock_questionnaire = Mock(vm_settings=mock_vm_settings)
        mock_job_answer_set = Mock(questionnaire=mock_questionnaire)
        self.assertEqual(4 * 20 + 10, calculate_volume_size(mock_job_answer_set))
