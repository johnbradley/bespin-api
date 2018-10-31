import json
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from data.tests_api import UserLogin
from data.models import Workflow, WorkflowVersion, WorkflowConfiguration, VMStrategy, ShareGroup, VMFlavor, VMSettings, \
    CloudSettings, VMProject, JobFileStageGroup, DDSUserCredential, DDSEndpoint, Job


class AdminWorkflowViewSetTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)

    def test_list_fails_unauthenticated(self):
        self.user_login.become_unauthorized()
        url = reverse('admin_workflow-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_fails_not_admin_user(self):
        self.user_login.become_normal_user()
        url = reverse('admin_workflow-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_with_admin_user(self):
        workflow = Workflow.objects.create(name='Exome Seq', tag='exomeseq')
        self.user_login.become_admin_user()
        url = reverse('admin_workflow-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], workflow.id)
        self.assertEqual(response.data[0]['name'], 'Exome Seq')
        self.assertEqual(response.data[0]['tag'], 'exomeseq')

    def test_retrieve_with_admin_user(self):
        workflow = Workflow.objects.create(name='Exome Seq', tag='exomeseq')
        self.user_login.become_admin_user()
        url = reverse('admin_workflow-list') + str(workflow.id) + '/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], workflow.id)
        self.assertEqual(response.data['name'], 'Exome Seq')
        self.assertEqual(response.data['tag'], 'exomeseq')

    def test_create_with_admin_user(self):
        self.user_login.become_admin_user()
        url = reverse('admin_workflow-list')
        response = self.client.post(url, format='json', data={
            'name': 'Exome Seq',
            'tag': 'exomeseq',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Exome Seq')
        self.assertEqual(response.data['tag'], 'exomeseq')
        workflows = Workflow.objects.all()
        self.assertEqual(len(workflows), 1)
        self.assertEqual(workflows[0].name, 'Exome Seq')
        self.assertEqual(workflows[0].tag, 'exomeseq')

    def test_put_fails_with_admin_user(self):
        workflow = Workflow.objects.create(name='Exome Seq', tag='exomeseq')
        self.user_login.become_admin_user()
        url = reverse('admin_workflow-list') + str(workflow.id) + '/'
        response = self.client.post(url, format='json', data={})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_fails_with_admin_user(self):
        workflow = Workflow.objects.create(name='Exome Seq', tag='exomeseq')
        self.user_login.become_admin_user()
        url = reverse('admin_workflow-list') + str(workflow.id) + '/'
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class AdminWorkflowVersionViewSetTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)
        self.workflow = Workflow.objects.create(name='Exome Seq', tag='exomeseq')

    def test_list_fails_unauthenticated(self):
        self.user_login.become_unauthorized()
        url = reverse('admin_workflowversion-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_fails_not_admin_user(self):
        self.user_login.become_normal_user()
        url = reverse('admin_workflowversion-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_with_admin_user(self):
        workflow_version = WorkflowVersion.objects.create(
            workflow=self.workflow,
            description='v1 exomeseq',
            version=1,
            url='',
            fields_json='[{"name":"threads", "class": "int"}]',
        )
        self.user_login.become_admin_user()
        url = reverse('admin_workflowversion-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], workflow_version.id)
        self.assertEqual(response.data[0]['workflow'], self.workflow.id)
        self.assertEqual(response.data[0]['description'], 'v1 exomeseq')
        self.assertEqual(response.data[0]['version'], 1)
        self.assertEqual(response.data[0]['fields'], [{"name": "threads", "class": "int"}])

    def test_retrieve_with_admin_user(self):
        workflow_version = WorkflowVersion.objects.create(
            workflow=self.workflow,
            description='v1 exomeseq',
            version=1,
            url='',
            fields_json='[{"name":"threads", "class": "int"}]',
        )
        self.user_login.become_admin_user()
        url = reverse('admin_workflowversion-list') + str(workflow_version.id) + '/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], workflow_version.id)
        self.assertEqual(response.data['workflow'], self.workflow.id)
        self.assertEqual(response.data['description'], 'v1 exomeseq')
        self.assertEqual(response.data['fields'], [{"name": "threads", "class": "int"}])

    def test_create_with_admin_user(self):
        self.user_login.become_admin_user()
        url = reverse('admin_workflowversion-list')
        response = self.client.post(url, format='json', data={
            'workflow': self.workflow.id,
            'description': 'v1 exomseq',
            'version': 2,
            'url': 'https://someurl.com',
            'fields': [{"name":"threads", "class": "int"}],

        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], 'v1 exomseq')
        workflow_versions = WorkflowVersion.objects.all()
        self.assertEqual(len(workflow_versions), 1)
        self.assertEqual(workflow_versions[0].version, 2)
        self.assertEqual(json.loads(workflow_versions[0].fields_json), [{"name": "threads", "class": "int"}])

    def test_put_fails_with_admin_user(self):
        self.user_login.become_admin_user()
        url = reverse('admin_workflowversion-list') + '1/'
        response = self.client.put(url, format='json', data={})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_fails_with_admin_user(self):
        self.user_login.become_admin_user()
        url = reverse('admin_workflowversion-list') + '1/'
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class AdminWorkflowConfigurationViewSetTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)
        self.workflow = Workflow.objects.create(name='Exome Seq', tag='exomeseq')
        self.workflow_version = WorkflowVersion.objects.create(
            workflow=self.workflow,
            description='v1 exomeseq',
            version=1,
            url='',
            fields_json='[{"name":"threads", "class": "int"}]'
        )
        vm_flavor = VMFlavor.objects.create(name='large')
        vm_project = VMProject.objects.create()
        cloud_settings = CloudSettings.objects.create(vm_project=vm_project)
        vm_settings = VMSettings.objects.create(cloud_settings=cloud_settings)

        self.vm_strategy = VMStrategy.objects.create(name='default', vm_flavor=vm_flavor, vm_settings=vm_settings)
        self.share_group = ShareGroup.objects.create()

    def test_list_fails_unauthenticated(self):
        self.user_login.become_unauthorized()
        url = reverse('admin_workflowconfiguration-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_fails_not_admin_user(self):
        self.user_login.become_normal_user()
        url = reverse('admin_workflowconfiguration-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_with_admin_user(self):
        workflow_configuration = WorkflowConfiguration.objects.create(
            name='b37xGen',
            workflow_version=self.workflow_version,
            system_job_order_json='{"A":"B"}',
            default_vm_strategy=self.vm_strategy,
            share_group=self.share_group,
        )
        self.user_login.become_admin_user()
        url = reverse('admin_workflowconfiguration-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], workflow_configuration.id)
        self.assertEqual(response.data[0]['name'], 'b37xGen')
        self.assertEqual(response.data[0]['tag'], 'exomeseq/v1/b37xGen')
        self.assertEqual(response.data[0]['workflow_version'], self.workflow_version.id)
        self.assertEqual(response.data[0]['system_job_order'], {"A": "B"})
        self.assertEqual(response.data[0]['default_vm_strategy'], self.vm_strategy.id)
        self.assertEqual(response.data[0]['share_group'], self.share_group.id)

    def test_retrieve_with_admin_user(self):
        workflow_configuration = WorkflowConfiguration.objects.create(
            name='b37xGen',
            workflow_version=self.workflow_version,
            system_job_order_json='{"A":"B"}',
            default_vm_strategy=self.vm_strategy,
            share_group=self.share_group,
        )
        self.user_login.become_admin_user()
        url = reverse('admin_workflowconfiguration-list') + str(workflow_configuration.id) + '/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], workflow_configuration.id)
        self.assertEqual(response.data['name'], 'b37xGen')
        self.assertEqual(response.data['tag'], 'exomeseq/v1/b37xGen')
        self.assertEqual(response.data['workflow_version'], self.workflow_version.id)
        self.assertEqual(response.data['system_job_order'], {"A": "B"})
        self.assertEqual(response.data['default_vm_strategy'], self.vm_strategy.id)
        self.assertEqual(response.data['share_group'], self.share_group.id)

    def test_create_with_admin_user(self):
        self.user_login.become_admin_user()
        url = reverse('admin_workflowconfiguration-list')
        response = self.client.post(url, format='json', data={
            'name': 'b37xGen',
            'workflow_version': self.workflow_version.id,
            'system_job_order': {"A": "B"},
            'default_vm_strategy': self.vm_strategy.id,
            'share_group': self.share_group.id,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'b37xGen')
        self.assertEqual(response.data['tag'], 'exomeseq/v1/b37xGen')
        self.assertEqual(response.data['system_job_order'], {"A": "B"})
        self.assertEqual(response.data['default_vm_strategy'], self.vm_strategy.id)
        self.assertEqual(response.data['share_group'], self.share_group.id)

    def test_put_fails_with_admin_user(self):
        self.user_login.become_admin_user()
        url = reverse('admin_workflowconfiguration-list') + '1/'
        response = self.client.put(url, format='json', data={})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_fails_with_admin_user(self):
        self.user_login.become_admin_user()
        url = reverse('admin_workflowconfiguration-list') + '1/'
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class VMStrategyViewSetTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)
        self.vm_flavor = VMFlavor.objects.create(name='large')
        vm_project = VMProject.objects.create()
        cloud_settings = CloudSettings.objects.create(vm_project=vm_project)
        self.vm_settings = VMSettings.objects.create(cloud_settings=cloud_settings)

    def test_list_fails_unauthenticated(self):
        self.user_login.become_unauthorized()
        url = reverse('vmstrategies-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_normal_user(self):
        self.vm_strategy = VMStrategy.objects.create(name='default', vm_flavor=self.vm_flavor,
                                                     vm_settings=self.vm_settings)
        self.user_login.become_normal_user()
        url = reverse('vmstrategies-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.vm_strategy.id)
        self.assertEqual(response.data[0]['name'], 'default')
        self.assertEqual(response.data[0]['vm_flavor'], self.vm_flavor.id)
        self.assertEqual(response.data[0]['vm_settings'], self.vm_settings.id)

    def test_retrieve_with_normal_user(self):
        self.vm_strategy = VMStrategy.objects.create(name='default', vm_flavor=self.vm_flavor,
                                                     vm_settings=self.vm_settings)
        self.user_login.become_normal_user()
        url = reverse('vmstrategies-list') + str(self.vm_strategy.id) + '/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.vm_strategy.id)
        self.assertEqual(response.data['name'], 'default')
        self.assertEqual(response.data['vm_flavor'], self.vm_flavor.id)
        self.assertEqual(response.data['vm_settings'], self.vm_settings.id)

    def test_post_fails_with_normal_user(self):
        self.user_login.become_normal_user()
        url = reverse('vmstrategies-list') + '1/'
        response = self.client.post(url, format='json', data={})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_fails_with_normal_user(self):
        self.user_login.become_normal_user()
        url = reverse('vmstrategies-list') + '1/'
        response = self.client.put(url, format='json', data={})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_fails_with_normal_user(self):
        self.user_login.become_normal_user()
        url = reverse('vmstrategies-list') + '1/'
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class WorkflowConfigurationViewSetTestCase(APITestCase):
    def setUp(self):
        self.user_login = UserLogin(self.client)
        self.workflow = Workflow.objects.create(name='Exome Seq', tag='exomeseq')
        self.workflow_version = WorkflowVersion.objects.create(
            workflow=self.workflow,
            description='v1 exomeseq',
            version=1,
            url='',
            fields_json='[{"name":"threads", "class": "int"},{"name":"items", "class": "int"}]',
        )
        self.workflow_version2 = WorkflowVersion.objects.create(
            workflow=self.workflow,
            description='v2 exomeseq',
            version=2,
            url='',
            fields_json='[{"name":"threads", "class": "int"}]',
        )
        vm_flavor = VMFlavor.objects.create(name='large')
        vm_project = VMProject.objects.create()
        cloud_settings = CloudSettings.objects.create(vm_project=vm_project)
        vm_settings = VMSettings.objects.create(cloud_settings=cloud_settings)

        self.vm_strategy = VMStrategy.objects.create(name='default', vm_flavor=vm_flavor, vm_settings=vm_settings)
        self.share_group = ShareGroup.objects.create()
        self.endpoint = DDSEndpoint.objects.create(name='DukeDS', agent_key='secret',
                                                   api_root='https://someserver.com/api')

    def test_list_fails_unauthenticated(self):
        self.user_login.become_unauthorized()
        url = reverse('workflowconfigurations-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_normal_user(self):
        workflow_configuration = WorkflowConfiguration.objects.create(
            name='b37xGen',
            workflow_version=self.workflow_version,
            system_job_order_json='{"A": "B"}',
            default_vm_strategy=self.vm_strategy,
            share_group=self.share_group,
        )
        self.user_login.become_normal_user()
        url = reverse('workflowconfigurations-list')
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], workflow_configuration.id)
        self.assertEqual(response.data[0]['name'], 'b37xGen')
        self.assertEqual(response.data[0]['tag'], 'exomeseq/v1/b37xGen')
        self.assertEqual(response.data[0]['workflow_version'], self.workflow_version.id)
        self.assertEqual(response.data[0]['system_job_order'], {"A": "B"})
        self.assertEqual(response.data[0]['default_vm_strategy'], self.vm_strategy.id)
        self.assertEqual(response.data[0]['share_group'], self.share_group.id)

    def test_list_normal_user_with_filtering(self):
        workflow_configuration1 = WorkflowConfiguration.objects.create(
            name='b37xGen',
            workflow_version=self.workflow_version,
            system_job_order_json='{"A": "B"}',
            default_vm_strategy=self.vm_strategy,
            share_group=self.share_group,
        )
        workflow_configuration2 = WorkflowConfiguration.objects.create(
            name='b37other',
            workflow_version=self.workflow_version2,
            system_job_order_json='{"A": "C"}',
            default_vm_strategy=self.vm_strategy,
            share_group=self.share_group,
        )
        self.user_login.become_normal_user()
        url = reverse('workflowconfigurations-list')
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data), 2)

        url = reverse('workflowconfigurations-list') + "?tag=exomeseq/v2/b37other"
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'b37other')

        url = reverse('workflowconfigurations-list') + "?workflow_version={}".format(self.workflow_version.id)
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'b37xGen')

    def test_create_job(self):
        workflow_configuration1 = WorkflowConfiguration.objects.create(
            name='b37xGen',
            workflow_version=self.workflow_version,
            system_job_order_json='{"A": "B"}',
            default_vm_strategy=self.vm_strategy,
            share_group=self.share_group,
        )
        user = self.user_login.become_normal_user()
        DDSUserCredential.objects.create(endpoint=self.endpoint, user=user, token='secret1', dds_id='1')
        stage_group = JobFileStageGroup.objects.create(user=user)
        url = reverse('workflowconfigurations-list') + "{}/create-job/".format(workflow_configuration1.id)
        response = self.client.post(url, format='json', data={
            'job_name': 'My Job',
            'fund_code': '001',
            'stage_group': stage_group.id,
            'user_job_order': {'color': 'red'},
            'job_vm_strategy': self.vm_strategy.id,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'My Job')

        jobs = Job.objects.all()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].name, 'My Job')
        self.assertEqual(jobs[0].fund_code, '001')
        self.assertEqual(jobs[0].job_order, '{"A": "B", "color": "red"}')

    def test_retrieve_normal_user(self):
        workflow_configuration = WorkflowConfiguration.objects.create(
            name='b37xGen',
            workflow_version=self.workflow_version,
            system_job_order_json='{"items": 4}',
            default_vm_strategy=self.vm_strategy,
            share_group=self.share_group,
        )
        self.user_login.become_normal_user()
        url = reverse('workflowconfigurations-list') + str(workflow_configuration.id) + '/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], workflow_configuration.id)
        self.assertEqual(response.data['name'], 'b37xGen')
        self.assertEqual(response.data['tag'], 'exomeseq/v1/b37xGen')
        self.assertEqual(response.data['workflow_version'], self.workflow_version.id)
        self.assertEqual(response.data['system_job_order'], {"items": 4})
        self.assertEqual(response.data['default_vm_strategy'], self.vm_strategy.id)
        self.assertEqual(response.data['share_group'], self.share_group.id)
        self.assertEqual(response.data['user_fields'], [{'name': 'threads', 'class': 'int'}])

    def test_create_with_admin_user(self):
        self.user_login.become_admin_user()
        url = reverse('workflowconfigurations-list')
        response = self.client.post(url, format='json', data={})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_fails_with_normal_user(self):
        self.user_login.become_normal_user()
        url = reverse('workflowconfigurations-list') + '1/'
        response = self.client.put(url, format='json', data={})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_fails_with_admin_user(self):
        self.user_login.become_normal_user()
        url = reverse('workflowconfigurations-list') + '1/'
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_create_with_admin_user(self):
        self.user_login.become_admin_user()
        url = reverse('workflowconfigurations-list')
        response = self.client.post(url, format='json', data={})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
