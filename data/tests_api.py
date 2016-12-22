from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User as django_user
from mock.mock import MagicMock, patch, Mock
from data.models import Workflow, WorkflowVersion, Job, JobInputFile, JobError, \
    DDSUserCredential, DDSEndpoint, DDSJobInputFile, URLJobInputFile, JobOutputDir
from exceptions import WrappedDataServiceException


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


class ProjectsTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)
        self.user_login.become_normal_user()

    def testFailsUnauthenticated(self):
        self.user_login.become_unauthorized()
        url = reverse('project-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('data.api.get_user_projects')
    def testListProjects(self, mock_get_user_projects):
        mock_get_user_projects.return_value = [Mock(id='abc123'), Mock(id='def567')]
        url = reverse('project-list')
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
        url = reverse('project-list') + project_id + '/'
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
        url = reverse('project-list') + project_id + '/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('data.api.get_user_project_content')
    def testRetrieveProjectContent(self, mock_get_user_project_content):
        project_id = 'abc123'
        mock_get_user_project_content.return_value = [{'id': '12355', 'name': 'test.txt'}]
        url = reverse('project-list') + project_id + '/content/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch('data.api.get_user_project_content')
    def testRetrieveProjectContentNotFound(self, mock_get_user_project_content):
        project_id = 'abc123'
        dds_error = MagicMock()
        dds_error.status_code = 404
        dds_error.message = 'Not Found'
        mock_get_user_project_content.side_effect = WrappedDataServiceException(dds_error)
        url = reverse('project-list') + project_id + '/content/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('data.api.get_user_project_content')
    def testRetrieveProjectContentWithFilter(self, mock_get_user_project_content):
        project_id = 'abc123'
        mock_get_user_project_content.return_value = [{'id': '12355', 'name': 'test.txt'}]
        url = reverse('project-list') + project_id + '/content/?search=test'
        response = self.client.get(url, format='json')
        mock, params = mock_get_user_project_content.call_args
        user, project_id, search = mock
        self.assertEqual('test', search)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


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
        self.assertEqual(1, len(response.data['results']))
        self.assertEqual('secret1', response.data['results'][0]['token'])

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
                                        'workflow_input_json': '{}',
                                    })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data['results']))
        self.assertEqual(normal_user.id, response.data['results'][0]['user'])
        self.assertEqual('my job', response.data['results'][0]['name'])

        other_user = self.user_login.become_other_normal_user()
        response = self.client.post(url, format='json',
                            data={
                                'name': 'my job2',
                                'workflow_version_id': self.workflow_version.id,
                                'vm_project_name': 'jpb88',
                                'workflow_input_json': '{}',
                            })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data['results']))
        self.assertEqual(other_user.id, response.data['results'][0]['user'])

    def testAdminSeeAllData(self):
        url = reverse('job-list')
        normal_user = self.user_login.become_normal_user()
        response = self.client.post(url, format='json',
                                    data={
                                        'name': 'my job',
                                        'workflow_version_id': self.workflow_version.id,
                                        'vm_project_name': 'jpb67',
                                        'workflow_input_json': '{}',
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
                                'workflow_input_json': '{}',
                            })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # admin user can see both via admin endpoint
        admin_user = self.user_login.become_admin_user()
        url = reverse('admin_job-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response.data['results']))
        self.assertIn(other_user.id, [item['user_id'] for item in response.data['results']])
        self.assertIn(normal_user.id, [item['user_id'] for item in response.data['results']])

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
                                        'workflow_input_json': '{}',
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
                                 workflow_input_json={},
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
                                 workflow_input_json={},
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
                                 workflow_input_json={},
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
                                 workflow_input_json={},
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
                                        'workflow_input_json': '{}',
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
                                       workflow_input_json='{}',
                                       user=other_user)
        JobInputFile.objects.create(job=other_job, file_type='dds_file', workflow_name='models')
        this_user = self.user_login.become_other_normal_user()
        this_job = Job.objects.create(workflow_version=self.workflow_version,
                                      vm_project_name='test',
                                      workflow_input_json='{}',
                                      user=this_user)
        JobInputFile.objects.create(job=this_job, file_type='dds_file', workflow_name='data1')

        # User endpoint only shows current user's data
        url = reverse('jobinputfile-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data['results']))

        # Admin endpoint shows all user's data
        self.user_login.become_admin_user()
        url = reverse('admin_jobinputfile-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response.data['results']))


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
                                       workflow_input_json='{}',
                                       user=other_user)
        JobError.objects.create(job=other_job, content='Out of memory.', job_step=Job.JOB_STEP_RUNNING)
        # Normal user can't write
        url = reverse('joberror-list')
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        my_user = self.user_login.become_other_normal_user()
        my_job = Job.objects.create(workflow_version=self.workflow_version,
                                       vm_project_name='test',
                                       workflow_input_json='{}',
                                       user=my_user)
        JobError.objects.create(job=my_job, content='Out of memory.', job_step=Job.JOB_STEP_RUNNING)

        # User endpoint only shows current user's data
        url = reverse('joberror-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data['results']))

        # Admin endpoint shows all user's data
        self.user_login.become_admin_user()
        url = reverse('admin_joberror-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response.data['results']))

    def testNormalEndpointNoWrite(self):
        self.user_login.become_normal_user()
        url = reverse('joberror-list')
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def testAdminEndpointCanWrite(self):
        my_user = self.user_login.become_admin_user()
        my_job = Job.objects.create(workflow_version=self.workflow_version,
                                       vm_project_name='test',
                                       workflow_input_json='{}',
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
                                       workflow_input_json='{}',
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
        self.assertEqual(1, len(response.data['results']))
        self.assertEqual('data.txt', response.data['results'][0]['destination_path'])

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
                                       workflow_input_json='{}',
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
        self.assertEqual(1, len(response.data['results']))
        self.assertEqual('http://stuff.com/data.txt', response.data['results'][0]['url'])


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
                                         workflow_input_json='{}',
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
        self.assertEqual(1, len(response.data['results']))
        job_output_dir = response.data['results'][0]
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


