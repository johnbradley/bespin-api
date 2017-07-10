from django.test import TestCase
from models import DDSEndpoint, DDSUserCredential
from models import Workflow, WorkflowVersion
from models import Job, JobFileStageGroup, DDSJobInputFile, URLJobInputFile, JobOutputDir, JobError
from models import LandoConnection
from models import JobQuestionnaire, JobAnswerSet, VMFlavor, VMProject
from models import JobToken
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import json

CWL_URL = 'https://raw.githubusercontent.com/johnbradley/iMADS-worker/master/predict_service/predict-workflow-packed.cwl'


class DDSEndpointTests(TestCase):
    # Not validating blank or null fields here, as it does not happen at the model layer
    # It is the responsibility of a form or serializer to do that.

    def test_unique_parameters1(self):
        endpoint1 = DDSEndpoint.objects.create(name='endpoint1', agent_key='abc123')
        self.assertIsNotNone(endpoint1)
        endpoint2 = DDSEndpoint.objects.create(name='endpoint2', agent_key='def456')
        self.assertIsNotNone(endpoint2)
        self.assertNotEqual(endpoint1, endpoint2)
        with self.assertRaises(IntegrityError):
            DDSEndpoint.objects.create(name='endpoint3', agent_key=endpoint1.agent_key)

    def test_unique_parameters2(self):
        DDSEndpoint.objects.create(name='endpoint1', agent_key='abc123')
        with self.assertRaises(IntegrityError):
            DDSEndpoint.objects.create(name='endpoint1', agent_key='ghi789')


class DDSUserCredentialTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test_user')
        self.endpoint = DDSEndpoint.objects.create(name='app1', agent_key='abc123')
        self.endpoint2 = DDSEndpoint.objects.create(name='app2', agent_key='abc124')

    def test_unique_parameters1(self):
        DDSUserCredential.objects.create(user=self.user, token='abc123', endpoint=self.endpoint)
        with self.assertRaises(IntegrityError):
            DDSUserCredential.objects.create(user=self.user, token='def456', endpoint=self.endpoint)

    def test_unique_parameters2(self):
        DDSUserCredential.objects.create(user=self.user, token='abc123', endpoint=self.endpoint)
        other_user = User.objects.create_user('other_user')
        with self.assertRaises(IntegrityError):
            DDSUserCredential.objects.create(user=other_user, token='abc123', endpoint=self.endpoint)

    def test_user_can_have_creds_for_diff_endpoints(self):
        DDSUserCredential.objects.create(user=self.user, token='abc123', endpoint=self.endpoint, dds_id='1')
        DDSUserCredential.objects.create(user=self.user, token='abc124', endpoint=self.endpoint2, dds_id='2')


class WorkflowTests(TestCase):
    def test_basic_functionality(self):
        Workflow.objects.create(name='RnaSeq')
        workflow = Workflow.objects.first()
        self.assertEqual('RnaSeq', workflow.name)


class WorkflowVersionTests(TestCase):
    def setUp(self):
        self.workflow = Workflow.objects.create(name='RnaSeq')

    def test_basic_functionality(self):
        WorkflowVersion.objects.create(workflow=self.workflow,
                                       object_name='#main',
                                       version='1',
                                       url=CWL_URL)
        workflow_version = WorkflowVersion.objects.first()
        self.assertEqual(self.workflow, workflow_version.workflow)
        self.assertEqual('#main', workflow_version.object_name)
        self.assertEqual(1, workflow_version.version)
        self.assertEqual(CWL_URL, workflow_version.url)
        self.assertIsNotNone(workflow_version.created)

    def test_default_object_name(self):
        WorkflowVersion.objects.create(workflow=self.workflow,
                                       version='1',
                                       url=CWL_URL)
        workflow_version = WorkflowVersion.objects.first()
        self.assertEqual('#main', workflow_version.object_name)

    def test_create_with_description(self):
        desc = """This is a detailed description of the job."""
        WorkflowVersion.objects.create(workflow=self.workflow, description=desc, version=1)
        wv = WorkflowVersion.objects.first()
        self.assertEqual(desc, wv.description)

    def test_version_num_and_workflow_are_unique(self):
        WorkflowVersion.objects.create(workflow=self.workflow, description="one", version=1)
        with self.assertRaises(IntegrityError):
            WorkflowVersion.objects.create(workflow=self.workflow, description="two", version=1)

    def test_sorted_by_version_num(self):
        WorkflowVersion.objects.create(workflow=self.workflow, description="two", version=2)
        a_workflow_version = WorkflowVersion.objects.create(workflow=self.workflow, description="one", version=1)
        WorkflowVersion.objects.create(workflow=self.workflow, description="three", version=3)
        versions = [wv.version for wv in WorkflowVersion.objects.all()]
        self.assertEqual([1, 2, 3], versions)
        a_workflow_version.version = 4
        a_workflow_version.save()
        versions = [wv.version for wv in WorkflowVersion.objects.all()]
        self.assertEqual([2, 3, 4], versions)


class JobTests(TestCase):
    def setUp(self):
        workflow = Workflow.objects.create(name='RnaSeq')
        self.workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                               object_name='#main',
                                                               version='1',
                                                               url=CWL_URL)
        self.user = User.objects.create_user('test_user')
        self.sample_json = "{'type': 1}"

    def test_create(self):
        Job.objects.create(workflow_version=self.workflow_version, user=self.user,
                           vm_project_name='jpb67',
                           job_order=self.sample_json)
        job = Job.objects.first()
        self.assertEqual(self.workflow_version, job.workflow_version)
        self.assertEqual(self.user, job.user)
        self.assertIsNotNone(job.created)
        self.assertEqual(Job.JOB_STATE_NEW, job.state)
        self.assertIsNotNone(job.last_updated)
        self.assertIsNotNone(job.vm_flavor)
        self.assertEqual(None, job.vm_instance_name)
        self.assertEqual('jpb67', job.vm_project_name)
        self.assertEqual(None, job.run_token)

    def test_create_with_name(self):
        Job.objects.create(name='Rna Seq for B-Lab', user=self.user)
        job = Job.objects.first()
        self.assertEqual('Rna Seq for B-Lab', job.name)

    def test_state_changes(self):
        # Create job which should start in new state
        Job.objects.create(workflow_version=self.workflow_version, user=self.user, job_order=self.sample_json)
        job = Job.objects.first()
        self.assertEqual(Job.JOB_STATE_NEW, job.state)

        # User enters token (authorizes running job)
        job.state = Job.JOB_STATE_AUTHORIZED
        job.run_token = JobToken.objects.create(token='secret-1')
        job.save()
        job = Job.objects.first()

        # Set state to create VM
        job.state = Job.JOB_STATE_RUNNING
        job_created = job.created
        job_updated = job.last_updated
        job.save()
        job = Job.objects.first()
        self.assertEqual(Job.JOB_STATE_RUNNING, job.state)
        # last_updated should have changed
        self.assertEqual(job_created, job.created)
        self.assertLess(job_updated, job.last_updated)

        # Set state to canceled
        job.state = Job.JOB_STATE_CANCEL
        job.save()
        job = Job.objects.first()
        self.assertEqual(Job.JOB_STATE_CANCEL, job.state)

    @staticmethod
    def add_job_fields(obj):
        obj.user = User.objects.create_user('test_user')
        obj.endpoint = DDSEndpoint.objects.create(name='app1', agent_key='abc123')
        obj.user_credentials = DDSUserCredential.objects.create(user=obj.user, token='abc123', endpoint=obj.endpoint)
        workflow = Workflow.objects.create(name='RnaSeq')
        obj.workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                               object_name='#main',
                                                               version='1',
                                                               url=CWL_URL)
        obj.sample_json = "{'type': 1}"
        obj.job = Job.objects.create(workflow_version=obj.workflow_version, user=obj.user,
                                     job_order=obj.sample_json)

    def test_sorted_by_created(self):
        j1 = Job.objects.create(workflow_version=self.workflow_version,
                                user=self.user,
                                job_order=self.sample_json)
        j2 = Job.objects.create(workflow_version=self.workflow_version,
                                user=self.user,
                                job_order=self.sample_json)
        j3 = Job.objects.create(workflow_version=self.workflow_version,
                                user=self.user,
                                job_order=self.sample_json)
        j4 = Job.objects.create(workflow_version=self.workflow_version,
                                user=self.user,
                                job_order=self.sample_json)
        job_ids = [job.id for job in Job.objects.all()]
        self.assertEqual([j1.id, j2.id, j3.id, j4.id], job_ids)
        j2.delete()
        j2 = Job.objects.create(workflow_version=self.workflow_version,
                                user=self.user,
                                job_order=self.sample_json)
        job_ids = [job.id for job in Job.objects.all()]
        self.assertEqual([j1.id, j3.id, j4.id, j2.id], job_ids)

    def test_fails_mismatch_stage_group_user(self):
        job = Job.objects.create(workflow_version=self.workflow_version, user=self.user,
                                 vm_project_name='jpb67',
                                 job_order=self.sample_json)
        other_user = User.objects.create_user('other_user')
        stage_group = JobFileStageGroup.objects.create(user=other_user)
        with self.assertRaises(ValidationError):
            job.stage_group = stage_group
            job.save()

    def test_create_with_run_job_token(self):
        job_token = JobToken.objects.create(token='test-this-1')
        job = Job.objects.create(workflow_version=self.workflow_version, user=self.user,
                                 vm_project_name='jpb67',
                                 job_order=self.sample_json,
                                 run_token=job_token)
        self.assertEqual(job.run_token, job_token)

    def test_save_then_set_run_job_token(self):
        job_token2 = JobToken.objects.create(token='test-this-2')
        job2 = Job.objects.create(workflow_version=self.workflow_version, user=self.user,
                                 vm_project_name='jpb67',
                                 job_order=self.sample_json)
        self.assertEqual(job2.run_token, None)
        job2.run_token = job_token2
        job2.save()

    def test_jobs_cant_share_job_tokens(self):
        job_token = JobToken.objects.create(token='test-this-1')
        job = Job.objects.create(workflow_version=self.workflow_version, user=self.user,
                                 vm_project_name='jpb67',
                                 job_order=self.sample_json,
                                 run_token=job_token)
        with self.assertRaises(IntegrityError) as raised_error:
            job2 = Job.objects.create(workflow_version=self.workflow_version, user=self.user,
                                     vm_project_name='jpb67',
                                     job_order=self.sample_json,
                                     run_token=job_token)
        self.assertTrue(str(raised_error.exception).startswith('UNIQUE constraint failed'))


class JobFileStageGroupTests(TestCase):

    def setUp(self):
        JobTests.add_job_fields(self)

    def test_dds_file(self):
        stage_group = JobFileStageGroup.objects.create(user=self.user)
        self.job.stage_group = stage_group
        self.job.save()
        DDSJobInputFile.objects.create(stage_group=stage_group,
                                       project_id='1234',
                                       file_id='5321',
                                       dds_user_credentials=self.user_credentials,
                                       destination_path='sample.fasta')
        # Test job fields
        stage_group = JobFileStageGroup.objects.first()
        self.assertEqual(self.job, stage_group.job)
        self.assertEqual(self.user, stage_group.user)

        # Test dds_files
        dds_files = stage_group.dds_files.all()
        self.assertEqual(1, len(dds_files))
        dds_file = dds_files[0]
        self.assertEqual(stage_group, dds_file.stage_group)
        self.assertEqual('1234', dds_file.project_id)
        self.assertEqual(self.user_credentials, dds_file.dds_user_credentials)
        self.assertEqual('sample.fasta', dds_file.destination_path)

    def test_url_file(self):
        stage_group = JobFileStageGroup.objects.create(user=self.user)
        self.job.stage_group = stage_group
        self.job.save()
        URLJobInputFile.objects.create(stage_group=stage_group,
                                       url='https://data.org/sample.fasta',
                                       destination_path='sample.fasta')

        # Test job fields
        stage_group = JobFileStageGroup.objects.first()
        self.assertEqual(self.job, stage_group.job)
        self.assertEqual(self.user, stage_group.user)

        # Test dds_files
        url_files = stage_group.url_files.all()
        self.assertEqual(1, len(url_files))
        url_file = url_files[0]
        self.assertEqual(stage_group, url_file.stage_group)
        self.assertEqual('https://data.org/sample.fasta', url_file.url)
        self.assertEqual('sample.fasta', url_file.destination_path)


class JobOutputDirTests(TestCase):
    def setUp(self):
        JobTests.add_job_fields(self)

    def test_basic_functionality(self):
        JobOutputDir.objects.create(job=self.job, dir_name='results', project_id='1234',
                                    dds_user_credentials=self.user_credentials)
        job_output_dir = JobOutputDir.objects.first()
        self.assertEqual(self.job, job_output_dir.job)
        self.assertEqual('results', job_output_dir.dir_name)
        self.assertEqual('1234', job_output_dir.project_id)
        self.assertEqual(self.user_credentials, job_output_dir.dds_user_credentials)


class LandoConnectionTests(TestCase):
    def test_basic_functionality(self):
        LandoConnection.objects.create(host='10.109.253.74', username='jpb67', password='secret', queue_name='lando')
        connection = LandoConnection.objects.first()
        self.assertEqual('10.109.253.74', connection.host)
        self.assertEqual('jpb67', connection.username)
        self.assertEqual('secret', connection.password)
        self.assertEqual('lando', connection.queue_name)


class JobErrorTests(TestCase):
    def setUp(self):
        JobTests.add_job_fields(self)

    def test_basic_functionality(self):
        JobError.objects.create(job=self.job,
                                content="Openstack ran out of floating IPs.",
                                job_step=Job.JOB_STEP_CREATE_VM)
        job_error = JobError.objects.first()
        self.assertEqual(self.job, job_error.job)
        self.assertEqual("Openstack ran out of floating IPs.", job_error.content)
        self.assertEqual(Job.JOB_STEP_CREATE_VM, job_error.job_step)
        self.assertIsNotNone(job_error.created)

class JobQuestionnaireTests(TestCase):

    @staticmethod
    def add_workflowversion_fields(obj):
        obj.user = User.objects.create_user('user')
        obj.workflow = Workflow.objects.create(name='RnaSeq')
        obj.workflow_version = WorkflowVersion.objects.create(workflow=obj.workflow,
                                                              object_name='#main',
                                                              version='1',
                                                              url=CWL_URL)
        obj.flavor1 = VMFlavor.objects.create(name='flavor1')
        obj.flavor2 = VMFlavor.objects.create(name='flavor2')
        obj.project = VMProject.objects.create(name='bespin-project')

    def setUp(self):
        self.add_workflowversion_fields(self)

    def test_two_questionnaires(self):
        questionnaire = JobQuestionnaire.objects.create(name='Ant RnaSeq',
                                                        description='Uses reference genome xyz and gene index abc',
                                                        workflow_version=self.workflow_version,
                                                        system_job_order_json='{"system_input": "foo"}',
                                                        vm_flavor=self.flavor1,
                                                        vm_project=self.project)
        questionnaire = JobQuestionnaire.objects.create(name='Human RnaSeq',
                                                        description='Uses reference genome zew and gene index def',
                                                        workflow_version=self.workflow_version,
                                                        system_job_order_json='{"system_input":"bar"}',
                                                        vm_flavor=self.flavor2,
                                                        vm_project=self.project)
        ant_questionnaire = JobQuestionnaire.objects.filter(name='Ant RnaSeq').first()
        self.assertEqual('Ant RnaSeq', ant_questionnaire.name)
        self.assertEqual('Uses reference genome xyz and gene index abc', ant_questionnaire.description)
        self.assertEqual('foo',json.loads(ant_questionnaire.system_job_order_json)['system_input'])
        self.assertEqual('flavor1', ant_questionnaire.vm_flavor.name)
        self.assertEqual('bespin-project', ant_questionnaire.vm_project.name)

        human_questionnaire = JobQuestionnaire.objects.filter(name='Human RnaSeq').first()
        self.assertEqual('Human RnaSeq', human_questionnaire.name)
        self.assertEqual('Uses reference genome zew and gene index def', human_questionnaire.description)
        self.assertEqual('bar',json.loads(human_questionnaire.system_job_order_json)['system_input'])
        self.assertEqual('flavor2', human_questionnaire.vm_flavor.name)
        self.assertEqual('bespin-project', human_questionnaire.vm_project.name)

class JobAnswerSetTests(TestCase):

    def setUp(self):
        JobQuestionnaireTests.add_workflowversion_fields(self)
        self.questionnaire = JobQuestionnaire.objects.create(name='Exome Seq Q',
                                                        description='Uses reference genome xyz and gene index abc',
                                                        workflow_version=self.workflow_version,
                                                        system_job_order_json='{"system_input": "foo"}',
                                                        vm_flavor=self.flavor1,
                                                        vm_project=self.project)
    def test_basic_functionality(self):
        JobAnswerSet.objects.create(user=self.user,
                                    questionnaire=self.questionnaire,
                                    job_name='job 1',
                                    user_job_order_json='{"user_input":"bar"}'
        )
        job_answer_set = JobAnswerSet.objects.first()
        self.assertEqual(self.user, job_answer_set.user),
        self.assertEqual(self.questionnaire, job_answer_set.questionnaire)
        self.assertEqual('job 1', job_answer_set.job_name)
        self.assertEqual('{"user_input":"bar"}', job_answer_set.user_job_order_json)


    def test_fails_mismatch_stage_group_user(self):
        job_answer_set = JobAnswerSet.objects.create(user=self.user,
                                                     questionnaire=self.questionnaire,
                                                     job_name='job 2',
                                                     user_job_order_json='{"user_input":"bar"}'
        )
        other_user = User.objects.create_user('other_user')
        stage_group = JobFileStageGroup.objects.create(user=other_user)
        with self.assertRaises(ValidationError):
            job_answer_set.stage_group = stage_group
            job_answer_set.save()


class JobTokenTests(TestCase):
    def test_create(self):
        self.assertEqual(0, len(JobToken.objects.all()))
        JobToken.objects.create(token='secret1')
        self.assertEqual(1, len(JobToken.objects.all()))
        JobToken.objects.create(token='secret2')
        job_tokens = [x.token for x in JobToken.objects.all()]
        self.assertIn('secret1', job_tokens)
        self.assertIn('secret2', job_tokens)
        self.assertEqual(2, len(job_tokens))

    def test_token_must_be_unique(self):
        JobToken.objects.create(token='secret1')
        with self.assertRaises(IntegrityError) as raised_error:
            JobToken.objects.create(token='secret1')
        self.assertTrue(str(raised_error.exception).startswith('UNIQUE constraint failed'))
