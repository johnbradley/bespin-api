from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User as django_user
from mock.mock import MagicMock, patch, Mock
from data.models import Workflow, WorkflowVersion, Job, JobInputFile, JobError, \
    DDSUserCredential, DDSEndpoint, DDSJobInputFile, URLJobInputFile, JobOutputDir, \
    JobQuestion, JobQuestionDataType, JobQuestionnaire, JobAnswer, JobStringAnswer, \
    JobAnswerSet, JobAnswerKind
from data.jobfactory import JOB_QUESTION_OUTPUT_DIRECTORY
from exceptions import WrappedDataServiceException
from util import DDSProject, DDSResource


class UserLogin(object):
    """
    Wraps up different user states for tests.
    """
    def __init__(self, client):
        self.client = client

    def become_unauthorized(self):
        self.client.logout()

    def become_normal_user(self):
        username = "user"
        password = "resu"
        user = django_user.objects.create_user(username=username, password=password)
        self.client.login(username=username, password=password)
        return user

    def become_other_normal_user(self):
        username = "user2"
        password = "resu2"
        user = django_user.objects.create_user(username=username, password=password)
        self.client.login(username=username, password=password)
        return user

    def become_admin_user(self):
        username = "myadmin"
        password = "nimda"
        user = django_user.objects.create_superuser(username=username, email='', password=password)
        self.client.login(username=username, password=password)
        return user


class DDSProjectsTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)
        self.user_login.become_normal_user()

    def testFailsUnauthenticated(self):
        self.user_login.become_unauthorized()
        url = reverse('dds-projects-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('data.api.get_user_projects')
    def testListProjects(self, mock_get_user_projects):
        mock_get_user_projects.return_value = [Mock(id='abc123'), Mock(id='def567')]
        url = reverse('dds-projects-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    @patch('data.api.get_user_project')
    def testRetrieveProject(self, mock_get_user_project):
        project_id = 'abc123'
        mock_dds_project = Mock()
        # name is special on instantiation, so configure()
        mock_dds_project.configure_mock(id=project_id, name='ProjectA')
        mock_get_user_project.return_value = mock_dds_project
        url = reverse('dds-projects-list') + project_id + '/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'ProjectA')

    @patch('data.api.get_user_project')
    def testRetrieveProjectNotFound(self, mock_get_user_project):
        project_id = 'abc123'
        dds_error = MagicMock()
        dds_error.status_code = 404
        dds_error.message = 'Not Found'
        mock_get_user_project.side_effect = WrappedDataServiceException(dds_error)
        url = reverse('dds-projects-list') + project_id + '/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DDSResourcesTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)
        self.user_login.become_normal_user()

    def testFailsUnauthenticated(self):
        self.user_login.become_unauthorized()
        url = reverse('dds-resources-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('data.api.get_user_project_content')
    def testListsResourcesByProject(self, mock_get_user_project_content):
        project_id = 'abc123'
        mock_get_user_project_content.return_value = DDSResource.from_list([{'id': '12355', 'name': 'test.txt', 'project': {'id': project_id}}])
        url = reverse('dds-resources-list')
        response = self.client.get(url, data={'project_id': project_id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch('data.api.get_user_folder_content')
    def testListsResourcesByFolder(self, mock_get_user_folder_content):
        project_id = 'abc123'
        folder_id = 'def456'
        mock_get_user_folder_content.return_value = DDSResource.from_list([{'id': '12355', 'name': 'test.txt', 'project': {'id': project_id}}])
        url = reverse('dds-resources-list')
        response = self.client.get(url, data={'folder_id': folder_id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch('data.api.get_user_project_content')
    def testFailsWhenProjectNotFound(self, mock_get_user_project_content):
        project_id = 'abc123'
        dds_error = MagicMock()
        dds_error.status_code = 404
        dds_error.message = 'Not Found'
        mock_get_user_project_content.side_effect = WrappedDataServiceException(dds_error)
        url = reverse('dds-resources-list')
        response = self.client.get(url, data={'project_id': project_id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def testFailsWithoutProjectOrFolderID(self):
        url = reverse('dds-resources-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DDSEndpointTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)

    def testNoPermissionsWithoutAuth(self):
        self.user_login.become_unauthorized()
        url = reverse('ddsendpoint-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DDSUserCredentialTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)
        self.endpoint = DDSEndpoint.objects.create(name='DukeDS', agent_key='secret',
                                                   api_root='https://someserver.com/api')

    def testNoPermissionsWithoutAuth(self):
        self.user_login.become_unauthorized()
        url = reverse('ddsusercredential-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def testUserOnlySeeTheirOwnCreds(self):
        other_user = self.user_login.become_other_normal_user()
        user = self.user_login.become_normal_user()
        self.cred = DDSUserCredential.objects.create(endpoint=self.endpoint, user=user, token='secret1')
        self.cred = DDSUserCredential.objects.create(endpoint=self.endpoint, user=other_user, token='secret2')
        self.assertEqual(2, len(DDSUserCredential.objects.all()))

        url = reverse('ddsusercredential-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data))
        self.assertEqual('secret1', response.data[0]['token'])

    def testUserCanCreate(self):
        user = self.user_login.become_normal_user()
        url = reverse('ddsusercredential-list')
        response = self.client.post(url, format='json', data={
            'endpoint': self.endpoint.id,
            'token': '12309ufwlkjasdf',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cred = DDSUserCredential.objects.first()
        self.assertEqual(user, cred.user)
        self.assertEqual('12309ufwlkjasdf', cred.token)


class WorkflowTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)

    def testNoPermissionsWithoutAuth(self):
        self.user_login.become_unauthorized()
        url = reverse('workflow-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def testReadOnlyForAuthUser(self):
        self.user_login.become_normal_user()
        url = reverse('workflow-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(url, format='json', data={'name': 'RnaSeq'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class WorkflowVersionTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)

    def testNoPermissionsWithoutAuth(self):
        self.user_login.become_unauthorized()
        url = reverse('workflowversion-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def testReadOnlyForAuthUser(self):
        self.user_login.become_normal_user()
        url = reverse('workflowversion-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class JobsTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)
        workflow = Workflow.objects.create(name='RnaSeq')
        cwl_url = "https://raw.githubusercontent.com/johnbradley/iMADS-worker/master/predict_service/predict-workflow-packed.cwl"
        self.workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                               version="1",
                                                               url=cwl_url)

    def testUserOnlySeeTheirData(self):
        url = reverse('job-list')
        normal_user = self.user_login.become_normal_user()
        response = self.client.post(url, format='json',
                                    data={
                                        'name': 'my job',
                                        'workflow_version_id': self.workflow_version.id,
                                        'vm_project_name': 'jpb67',
                                        'job_order': '{}',
                                    })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data))
        self.assertEqual(normal_user.id, response.data[0]['user'])
        self.assertEqual('my job', response.data[0]['name'])

        other_user = self.user_login.become_other_normal_user()
        response = self.client.post(url, format='json',
                            data={
                                'name': 'my job2',
                                'workflow_version_id': self.workflow_version.id,
                                'vm_project_name': 'jpb88',
                                'job_order': '{}',
                            })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data))
        self.assertEqual(other_user.id, response.data[0]['user'])

    def testAdminSeeAllData(self):
        url = reverse('job-list')
        normal_user = self.user_login.become_normal_user()
        response = self.client.post(url, format='json',
                                    data={
                                        'name': 'my job',
                                        'workflow_version_id': self.workflow_version.id,
                                        'vm_project_name': 'jpb67',
                                        'job_order': '{}',
                                    })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # normal user can't see admin endpoint
        url = reverse('admin_job-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        other_user = self.user_login.become_other_normal_user()
        url = reverse('job-list')
        response = self.client.post(url, format='json',
                            data={
                                'name': 'my job2',
                                'workflow_version_id': self.workflow_version.id,
                                'vm_project_name': 'jpb88',
                                'job_order': '{}',
                            })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # admin user can see both via admin endpoint
        admin_user = self.user_login.become_admin_user()
        url = reverse('admin_job-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response.data))
        self.assertIn(other_user.id, [item['user_id'] for item in response.data])
        self.assertIn(normal_user.id, [item['user_id'] for item in response.data])

    def testStopRegularUserFromSettingStateOrStep(self):
        """
        Only admin should change job state or job step.
        """
        url = reverse('job-list')
        normal_user = self.user_login.become_normal_user()
        response = self.client.post(url, format='json',
                                    data={
                                        'name': 'my job',
                                        'workflow_version_id': self.workflow_version.id,
                                        'vm_project_name': 'jpb67',
                                        'job_order': '{}',
                                        'state': Job.JOB_STATE_FINISHED,
                                        'step': Job.JOB_STEP_RUNNING,
                                    })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        job = Job.objects.first()
        self.assertEqual(Job.JOB_STATE_NEW, job.state)
        self.assertEqual(None, job.step)

    def testAdminUserUpdatesStateAndStep(self):
        """
        Admin should be able to change job state and job step.
        """
        admin_user = self.user_login.become_admin_user()
        job = Job.objects.create(workflow_version=self.workflow_version,
                                 vm_project_name='jpb67',
                                 job_order={},
                                 user=admin_user)
        url = reverse('admin_job-list') + '{}/'.format(job.id)
        response = self.client.put(url, format='json',
                                    data={
                                        'state': Job.JOB_STATE_RUNNING,
                                        'step': Job.JOB_STEP_CREATE_VM,
                                    })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        job = Job.objects.first()
        self.assertEqual(Job.JOB_STATE_RUNNING, job.state)
        self.assertEqual(Job.JOB_STEP_CREATE_VM, job.step)

    @patch('data.lando.LandoJob._make_client')
    def test_job_start(self, mock_make_client):
        normal_user = self.user_login.become_normal_user()
        job = Job.objects.create(workflow_version=self.workflow_version,
                                 vm_project_name='jpb67',
                                 job_order={},
                                 user=normal_user)

        url = reverse('job-list') + str(job.id) + '/start/'

        # Post to /start/ for job in NEW state should work
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Post to /start/ for job in RUNNING state should fail
        job.state = Job.JOB_STATE_RUNNING
        job.save()
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('data.lando.LandoJob._make_client')
    def test_job_cancel(self, mock_make_client):
        normal_user = self.user_login.become_normal_user()
        job = Job.objects.create(workflow_version=self.workflow_version,
                                 vm_project_name='jpb67',
                                 job_order={},
                                 user=normal_user)
        url = reverse('job-list') + str(job.id) + '/cancel/'
        # Post to /cancel/ for job should work
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('data.lando.LandoJob._make_client')
    def test_job_restart(self, mock_make_client):
        normal_user = self.user_login.become_normal_user()
        job = Job.objects.create(workflow_version=self.workflow_version,
                                 vm_project_name='jpb67',
                                 job_order={},
                                 user=normal_user)
        url = reverse('job-list') + str(job.id) + '/restart/'

        # Post to /restart/ for job in NEW state should fail (user should use /start/)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_make_client().restart_job.assert_not_called()

        # Post to /restart/ for job in ERROR state should work
        job.state = Job.JOB_STATE_ERROR
        job.save()
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_make_client().restart_job.assert_called_with(str(1))

        # Post to /restart/ for job in CANCEL state should work
        job.state = Job.JOB_STATE_CANCEL
        job.save()
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def testJobAutoFillsInUser(self):
        url = reverse('job-list')
        normal_user = self.user_login.become_normal_user()
        response = self.client.post(url, format='json',
                                    data={
                                        'name': 'my job',
                                        'workflow_version_id': self.workflow_version.id,
                                        'vm_project_name': 'jpb67',
                                        'job_order': '{}',
                                    })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        job = Job.objects.first()
        self.assertEqual(job.user, normal_user)


class JobInputFilesTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)
        workflow = Workflow.objects.create(name='RnaSeq')
        cwl_url = "https://raw.githubusercontent.com/johnbradley/iMADS-worker/master/predict_service/predict-workflow-packed.cwl"
        self.workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                               version="1",
                                                               url=cwl_url)

    def testOnlySeeOwnJobInputFiles(self):
        other_user = self.user_login.become_normal_user()
        other_job = Job.objects.create(workflow_version=self.workflow_version,
                                       vm_project_name='test',
                                       job_order='{}',
                                       user=other_user)
        JobInputFile.objects.create(job=other_job, file_type='dds_file', workflow_name='models')
        this_user = self.user_login.become_other_normal_user()
        this_job = Job.objects.create(workflow_version=self.workflow_version,
                                      vm_project_name='test',
                                      job_order='{}',
                                      user=this_user)
        JobInputFile.objects.create(job=this_job, file_type='dds_file', workflow_name='data1')

        # User endpoint only shows current user's data
        url = reverse('jobinputfile-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data))

        # Admin endpoint shows all user's data
        self.user_login.become_admin_user()
        url = reverse('admin_jobinputfile-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response.data))


class JobErrorTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)
        workflow = Workflow.objects.create(name='RnaSeq')
        cwl_url = "https://raw.githubusercontent.com/johnbradley/iMADS-worker/master/predict_service/predict-workflow-packed.cwl"
        self.workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                               version="1",
                                                               url=cwl_url)

    def testNormalUserReadOnly(self):
        other_user = self.user_login.become_normal_user()
        other_job = Job.objects.create(workflow_version=self.workflow_version,
                                       vm_project_name='test',
                                       job_order='{}',
                                       user=other_user)
        JobError.objects.create(job=other_job, content='Out of memory.', job_step=Job.JOB_STEP_RUNNING)
        # Normal user can't write
        url = reverse('joberror-list')
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        my_user = self.user_login.become_other_normal_user()
        my_job = Job.objects.create(workflow_version=self.workflow_version,
                                       vm_project_name='test',
                                       job_order='{}',
                                       user=my_user)
        JobError.objects.create(job=my_job, content='Out of memory.', job_step=Job.JOB_STEP_RUNNING)

        # User endpoint only shows current user's data
        url = reverse('joberror-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data))

        # Admin endpoint shows all user's data
        self.user_login.become_admin_user()
        url = reverse('admin_joberror-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response.data))

    def testNormalEndpointNoWrite(self):
        self.user_login.become_normal_user()
        url = reverse('joberror-list')
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def testAdminEndpointCanWrite(self):
        my_user = self.user_login.become_admin_user()
        my_job = Job.objects.create(workflow_version=self.workflow_version,
                                       vm_project_name='test',
                                       job_order='{}',
                                       user=my_user)
        url = reverse('admin_joberror-list')
        response = self.client.post(url, format='json', data={
            'job': my_job.id,
            'content': 'oops',
            'job_step': Job.JOB_STEP_CREATE_VM,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(1, len(JobError.objects.all()))


class DDSJobInputFileTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)
        workflow = Workflow.objects.create(name='RnaSeq')
        cwl_url = "https://raw.githubusercontent.com/johnbradley/iMADS-worker/master/predict_service/predict-workflow-packed.cwl"
        self.workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                               version="1",
                                                               url=cwl_url)
        self.other_user = self.user_login.become_other_normal_user()
        self.my_user = self.user_login.become_normal_user()
        self.my_job = Job.objects.create(workflow_version=self.workflow_version,
                                       vm_project_name='test',
                                       job_order='{}',
                                       user=self.my_user)
        self.job_input_file = JobInputFile.objects.create(job=self.my_job, file_type='dds_file', workflow_name='data1')
        endpoint = DDSEndpoint.objects.create(name='DukeDS', agent_key='secret', api_root='https://someserver.com/api')
        self.cred = DDSUserCredential.objects.create(endpoint=endpoint, user=self.my_user, token='secret2')
        self.other_cred = DDSUserCredential.objects.create(endpoint=endpoint, user=self.other_user, token='secret3')

    def testPostAndRead(self):
        url = reverse('ddsjobinputfile-list')
        response = self.client.post(url, format='json', data={
            'job_input_file': self.job_input_file.id,
            'project_id': '12356',
            'file_id': '345987',
            'dds_user_credentials': self.cred.id,
            'destination_path': 'data.txt',
            'index': '1',

        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(1, len(DDSJobInputFile.objects.all()))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data))
        self.assertEqual('data.txt', response.data[0]['destination_path'])

    def testUsingOthersCreds(self):
        url = reverse('ddsjobinputfile-list')
        response = self.client.post(url, format='json', data={
            'job_input_file': self.job_input_file.id,
            'project_id': '12356',
            'file_id': '345987',
            'dds_user_credentials': self.other_cred.id,
            'destination_path': 'data.txt',
            'index': '1',

        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class URLJobInputFileTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)
        workflow = Workflow.objects.create(name='RnaSeq')
        cwl_url = "https://raw.githubusercontent.com/johnbradley/iMADS-worker/master/predict_service/predict-workflow-packed.cwl"
        self.workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                               version="1",
                                                               url=cwl_url)
        self.my_user = self.user_login.become_normal_user()
        self.my_job = Job.objects.create(workflow_version=self.workflow_version,
                                         vm_project_name='test',
                                         job_order='{}',
                                         user=self.my_user)
        self.job_input_file = JobInputFile.objects.create(job=self.my_job, file_type='dds_file', workflow_name='data1')

    def testPostAndRead(self):
        url = reverse('urljobinputfile-list')
        response = self.client.post(url, format='json', data={
            'job_input_file': self.job_input_file.id,
            'url': 'http://stuff.com/data.txt',
            'destination_path': 'data.txt',
            'index': '1',

        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(1, len(URLJobInputFile.objects.all()))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data))
        self.assertEqual('http://stuff.com/data.txt', response.data[0]['url'])


class JobOutputDirTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)
        workflow = Workflow.objects.create(name='RnaSeq')
        cwl_url = "https://raw.githubusercontent.com/johnbradley/iMADS-worker/master/predict_service/predict-workflow-packed.cwl"
        self.workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                               version="1",
                                                               url=cwl_url)
        self.other_user = self.user_login.become_other_normal_user()
        self.my_user = self.user_login.become_normal_user()
        self.my_job = Job.objects.create(workflow_version=self.workflow_version,
                                         vm_project_name='test',
                                         job_order='{}',
                                         user=self.my_user)

        self.endpoint = DDSEndpoint.objects.create(name='DukeDS', agent_key='secret', api_root='https://someserver.com/api')
        self.cred = DDSUserCredential.objects.create(endpoint=self.endpoint, user=self.my_user, token='secret2')
        self.others_cred = DDSUserCredential.objects.create(endpoint=self.endpoint, user=self.other_user, token='secret3')

    def test_list_dirs(self):
        JobOutputDir.objects.create(job=self.my_job, dir_name='results', project_id='1',
                                    dds_user_credentials=self.cred)
        url = reverse('joboutputdir-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data))
        job_output_dir = response.data[0]
        self.assertEqual(self.my_job.id, job_output_dir['job'])
        self.assertEqual('results', job_output_dir['dir_name'])
        self.assertEqual('1', job_output_dir['project_id'])
        self.assertEqual(self.cred.id, job_output_dir['dds_user_credentials'])

    def test_create(self):
        url = reverse('joboutputdir-list')
        response = self.client.post(url, format='json', data={
            'job': self.my_job.id,
            'dir_name': 'results',
            'project_id': '123',
            'dds_user_credentials': self.cred.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        job_output_dir = JobOutputDir.objects.first()
        self.assertEqual(self.my_job, job_output_dir.job)
        self.assertEqual('results', job_output_dir.dir_name)
        self.assertEqual('123', job_output_dir.project_id)
        self.assertEqual(self.cred, job_output_dir.dds_user_credentials)

    def test_cant_use_others_creds(self):
        url = reverse('joboutputdir-list')
        response = self.client.post(url, format='json', data={
            'job': self.my_job.id,
            'dir_name': 'results',
            'project_id': '123',
            'dds_user_credentials': self.others_cred.id
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class JobQuestionTestCase(APITestCase):
    def setUp(self):
        """
        Create some questions since this should be a read only endpoint.
        """
        self.user_login = UserLogin(self.client)
        self.ques1 = JobQuestion.objects.create(key="align_out_prefix", data_type=JobQuestionDataType.STRING,
                                                name="Output file prefix")
        JobQuestion.objects.create(key="gff_file", data_type=JobQuestionDataType.FILE)
        JobQuestion.objects.create(key="reads", data_type=JobQuestionDataType.FILE, occurs=2)
        JobQuestion.objects.create(key="threads", data_type=JobQuestionDataType.INTEGER)

    def test_user_can_read(self):
        self.user_login.become_normal_user()
        url = reverse('jobquestion-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(4, len(response.data))

        response = self.client.get('{}{}/'.format(url, self.ques1.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('align_out_prefix', response.data['key'])
        self.assertEqual('Output file prefix', response.data['name'])
        self.assertEqual('string', response.data['data_type'])
        self.assertEqual(1, response.data['occurs'])

    def test_user_cant_write(self):
        self.user_login.become_normal_user()
        url = reverse('jobquestion-list')
        response = self.client.post(url, format='json', data={
            'key': 'index',
            'data_type': 'string',
            'name': 'testing'
        })
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        ques_1_endpoint = '{}{}/'.format(url, self.ques1.id)
        response = self.client.put(ques_1_endpoint, format='json', data={
            'key': 'index',
            'data_type': 'string',
            'name': 'testing'
        })
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class JobQuestionnaireTestCase(APITestCase):
    def setUp(self):
        """
        Create two questionnaires since this should be a read only endpoint.
        """
        self.user_login = UserLogin(self.client)
        workflow = Workflow.objects.create(name='RnaSeq')
        cwl_url = "https://raw.githubusercontent.com/johnbradley/iMADS-worker/master/predict_service/predict-workflow-packed.cwl"
        self.workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                               version="1",
                                                               url=cwl_url)
        self.ques1 = JobQuestion.objects.create(key="align_out_prefix", data_type=JobQuestionDataType.STRING,
                                                name="Output file prefix")
        self.ques2 = JobQuestion.objects.create(key="gff_file", data_type=JobQuestionDataType.FILE)
        self.ques3 = JobQuestion.objects.create(key="reads", data_type=JobQuestionDataType.FILE, occurs=2)
        self.ques4 = JobQuestion.objects.create(key="threads", data_type=JobQuestionDataType.INTEGER)

        self.questionnaire1 = JobQuestionnaire.objects.create(description='Workflow1',
                                                              workflow_version=self.workflow_version)
        self.questionnaire1.questions = [self.ques1, self.ques2, self.ques3, self.ques4]
        self.questionnaire1.save()

        self.questionnaire2 = JobQuestionnaire.objects.create(description='Workflow2',
                                                              workflow_version=self.workflow_version)
        self.questionnaire2.questions = [self.ques2, self.ques3]
        self.questionnaire2.save()

    def test_user_can_read(self):
        self.user_login.become_normal_user()
        url = reverse('jobquestionnaire-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response.data))

        url = '{}{}/'.format(reverse('jobquestionnaire-list'), self.questionnaire1.id)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('Workflow1', response.data['description'])
        self.assertEqual(self.workflow_version.id, response.data['workflow_version'])
        self.assertEqual(4, len(response.data['questions']))
        self.assertEqual(self.ques1.id, response.data['questions'][0])

        url = '{}{}/'.format(reverse('jobquestionnaire-list'), self.questionnaire2.id)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('Workflow2', response.data['description'])
        self.assertEqual(self.workflow_version.id, response.data['workflow_version'])
        self.assertEqual(2, len(response.data['questions']))
        self.assertEqual(self.ques2.id, response.data['questions'][0])

    def test_user_cant_write(self):
        self.user_login.become_normal_user()
        url = reverse('jobquestionnaire-list')
        response = self.client.post(url, format='json', data={
            'description': 'Workflow3',
            'workflow_version': self.workflow_version.id
        })
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        questionnaire1_endpoint = '{}{}/'.format(url, self.questionnaire1.id)
        response = self.client.put(questionnaire1_endpoint, format='json', data={
            'description': 'Workflow3',
            'workflow_version': self.workflow_version.id
        })
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class JobAnswerTestCase(APITestCase):
    def setUp(self):
        self.endpoint = DDSEndpoint.objects.create(name='DukeDS', agent_key='secret',
                                                   api_root='https://someserver.com/api')
        self.user_login = UserLogin(self.client)
        self.ques1 = JobQuestion.objects.create(key="align_out_prefix", data_type=JobQuestionDataType.STRING,
                                                name="Output file prefix")
        workflow = Workflow.objects.create(name='RnaSeq')
        cwl_url = "https://raw.githubusercontent.com/johnbradley/iMADS-worker/master/predict_service/predict-workflow-packed.cwl"
        self.workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                               version="1",
                                                               url=cwl_url)
        self.questionnaire1 = JobQuestionnaire.objects.create(description='Workflow1',
                                                              workflow_version=self.workflow_version)

    def test_can_create_string_value(self):
        self.user_login.become_normal_user()

        # user creates a JobAnswer and JobAnswerString
        url = reverse('jobanswer-list')
        response = self.client.post(url, format='json', data={
            'question': self.ques1.id,
            'kind': JobAnswerKind.STRING,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        answer_id = response.data['id']
        self.assertEqual(1, answer_id)

        url = reverse('jobstringanswer-list')
        response = self.client.post(url, format='json', data={
            'answer': answer_id,
            'value': 'results_ant_1_',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # database is correct
        job_answer = JobAnswer.objects.first()
        self.assertEqual('string', job_answer.kind)
        job_string_answer = JobStringAnswer.objects.filter(answer=job_answer).first()
        self.assertEqual('results_ant_1_', job_string_answer.value)

        # user can change value
        url = '{}{}/'.format(reverse('jobstringanswer-list'), job_answer.id)
        response = self.client.put(url, format='json', data={
            'answer': answer_id,
            'value': 'results_ant_2_',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # database is correct
        job_string_answer = JobStringAnswer.objects.filter(answer=job_answer).first()
        self.assertEqual('results_ant_2_', job_string_answer.value)

    def test_can_create_dds_value(self):
        user = self.user_login.become_normal_user()
        self.cred = DDSUserCredential.objects.create(endpoint=self.endpoint, user=user, token='secret1')

        # user creates a JobAnswer and JobDDSFileAnswer
        url = reverse('jobanswer-list')
        response = self.client.post(url, format='json', data={
            'question': self.ques1.id,
            'kind': JobAnswerKind.DDS_FILE,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        answer_id = response.data['id']
        self.assertEqual(1, answer_id)

        url = reverse('jobddsfileanswer-list')
        response = self.client.post(url, format='json', data={
            'answer': answer_id,
            'project_id': '123',
            'file_id': '4321',
            'dds_user_credentials': self.cred.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_mismatch_string_with_dds_fails(self):
        user = self.user_login.become_normal_user()
        self.cred = DDSUserCredential.objects.create(endpoint=self.endpoint, user=user, token='secret1')

        # user creates a JobAnswer and JobDDSFileAnswer
        url = reverse('jobanswer-list')
        response = self.client.post(url, format='json', data={
            'question': self.ques1.id,
            'kind': JobAnswerKind.STRING,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        answer_id = response.data['id']
        self.assertEqual(1, answer_id)

        url = reverse('jobddsfileanswer-list')
        response = self.client.post(url, format='json', data={
            'answer': answer_id,
            'project_id': '123',
            'file_id': '4321',
            'dds_user_credentials': self.cred.id
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mismatch_dds_with_string_fails(self):
        self.user_login.become_normal_user()

        # user creates a JobAnswer and JobAnswerString
        url = reverse('jobanswer-list')
        response = self.client.post(url, format='json', data={
            'question': self.ques1.id,
            'kind': JobAnswerKind.DDS_FILE,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        answer_id = response.data['id']
        self.assertEqual(1, answer_id)

        url = reverse('jobstringanswer-list')
        response = self.client.post(url, format='json', data={
            'answer': answer_id,
            'value': 'results_ant_1_',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_cant_assign_questionnaire(self):
        # Users can't create system answers
        self.user_login.become_normal_user()
        url = reverse('jobanswer-list')
        response = self.client.post(url, format='json', data={
            'question': self.ques1.id,
            'kind': JobAnswerKind.DDS_FILE,
            'questionnaire': self.questionnaire1.id
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_cant_change_system_answers(self):
        user = self.user_login.become_normal_user()
        question = JobQuestion.objects.create(key="align_out_prefix", data_type=JobQuestionDataType.STRING)
        sys_job_answer = JobAnswer.objects.create(question=question, questionnaire=self.questionnaire1, user=user)
        url = '{}{}/'.format(reverse('jobanswer-list'), sys_job_answer.id)
        response = self.client.put(url, format='json', data={
            'question': self.ques1.id,
            'kind': JobAnswerKind.DDS_FILE,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class JobAnswerSetTests(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)
        workflow = Workflow.objects.create(name='RnaSeq')
        cwl_url = "https://raw.githubusercontent.com/johnbradley/iMADS-worker/master/predict_service/predict-workflow-packed.cwl"
        self.workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                               version="1",
                                                               url=cwl_url)
        self.questionnaire1 = JobQuestionnaire.objects.create(description='Workflow1',
                                                              workflow_version=self.workflow_version)
        self.questionnaire2 = JobQuestionnaire.objects.create(description='Workflow1',
                                                              workflow_version=self.workflow_version)
        self.other_user = self.user_login.become_other_normal_user()
        self.user = self.user_login.become_normal_user()
        question = JobQuestion.objects.create(key="align_out_prefix", data_type=JobQuestionDataType.STRING)
        self.questionnaire1.questions = [question]
        self.questionnaire1.save()
        other_question = JobQuestion.objects.create(key="something", data_type=JobQuestionDataType.STRING)
        self.other_answer = JobAnswer.objects.create(question=question, questionnaire=self.questionnaire2, user=self.user)
        self.system_answer = JobAnswer.objects.create(question=question, questionnaire=self.questionnaire1, user=self.user)
        self.user_answer1 = JobAnswer.objects.create(question=question, user=self.user)
        self.user_answer2 = JobAnswer.objects.create(question=question, user=self.user)
        self.other_user_answer = JobAnswer.objects.create(question=question, user=self.other_user)

    def test_user_crud(self):
        url = reverse('jobanswerset-list')
        response = self.client.post(url, format='json', data={
            'questionnaire': self.questionnaire1.id,
            'answers': [],
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(1, len(JobAnswerSet.objects.all()))
        job_answer_set = JobAnswerSet.objects.first()
        answers = job_answer_set.answers.all()
        self.assertEqual(0, len(answers))

        url = '{}{}/'.format(reverse('jobanswerset-list'), response.data['id'])
        response = self.client.put(url, format='json', data={
            'questionnaire': self.questionnaire1.id,
            'answers': [self.user_answer1.id, self.user_answer2.id],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        job_answer_set = JobAnswerSet.objects.first()
        answers = job_answer_set.answers.all()
        self.assertEqual(2, len(answers))
        self.assertEqual(self.user_answer1.id, answers[0].id)

        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(0, len(JobAnswerSet.objects.all()))

    def test_cant_use_system_answers(self):
        url = reverse('jobanswerset-list')
        response = self.client.post(url, format='json', data={
            'questionnaire': self.questionnaire1.id,
            'answers': [self.system_answer.id],
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_use_another_users_answers(self):
        url = reverse('jobanswerset-list')
        response = self.client.post(url, format='json', data={
            'questionnaire': self.questionnaire1.id,
            'answers': [self.other_user_answer.id],
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_use_answer_for_other_questionnaire(self):
        url = reverse('jobanswerset-list')
        response = self.client.post(url, format='json', data={
            'questionnaire': self.questionnaire1.id,
            'answers': [self.other_answer.id],
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class JobDDSOutputDirectoryAnswerTests(APITestCase):
    def setUp(self):
        self.endpoint = DDSEndpoint.objects.create(name='DukeDS', agent_key='secret',
                                                   api_root='https://someserver.com/api')
        self.user_login = UserLogin(self.client)
        self.ques1 = JobQuestion.objects.create(key="align_out_prefix", data_type=JobQuestionDataType.STRING,
                                                name="Output file prefix")
        workflow = Workflow.objects.create(name='RnaSeq')
        cwl_url = "https://raw.githubusercontent.com/johnbradley/iMADS-worker/master/predict_service/predict-workflow-packed.cwl"
        self.workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                               version="1",
                                                               url=cwl_url)
        self.questionnaire1 = JobQuestionnaire.objects.create(description='Workflow1',
                                                              workflow_version=self.workflow_version)

    def test_using_own_credentials(self):
        user = self.user_login.become_normal_user()
        user_cred = DDSUserCredential.objects.create(endpoint=self.endpoint, user=user, token='secret2')
        question = JobQuestion.objects.create(key=JOB_QUESTION_OUTPUT_DIRECTORY,
                                              data_type=JobQuestionDataType.DIRECTORY)
        answer = JobAnswer.objects.create(question=question, questionnaire=self.questionnaire1, user=user,
                                          kind=JobAnswerKind.DDS_OUTPUT_DIRECTORY)
        url = reverse('jobddsoutputdirectoryanswer-list')
        response = self.client.post(url, format='json', data={
            'dds_user_credentials': user_cred.id,
            'answer': answer.id,
            'project_id': '123',
            'directory_name': 'results',

        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_using_others_credentials(self):
        other_user = self.user_login.become_other_normal_user()
        other_user_cred = DDSUserCredential.objects.create(endpoint=self.endpoint, user=other_user, token='secret2')
        user = self.user_login.become_normal_user()
        question = JobQuestion.objects.create(key=JOB_QUESTION_OUTPUT_DIRECTORY,
                                              data_type=JobQuestionDataType.DIRECTORY)
        answer = JobAnswer.objects.create(question=question, questionnaire=self.questionnaire1, user=user,
                                          kind=JobAnswerKind.DDS_OUTPUT_DIRECTORY)
        url = reverse('jobddsoutputdirectoryanswer-list')
        response = self.client.post(url, format='json', data={
            'dds_user_credentials': other_user_cred.id,
            'answer': answer.id,
            'project_id': '123',
            'directory_name': 'results',

        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You cannot use another user\'s credentials.', response.data['non_field_errors'])
