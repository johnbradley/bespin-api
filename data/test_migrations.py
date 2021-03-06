"""
TestMigrations from https://www.caktusgroup.com/blog/2016/02/02/writing-unit-tests-django-migrations/
"""
from django.apps import apps
from django.test import TransactionTestCase
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
from django.core.management import call_command


class TestMigrations(TransactionTestCase):
    """
    Modifies setUp to migrate to the migration name in `migrate_from` then run `setUpBeforeMigration(apps)`
    finally finishes migrating to `migrate_to`. Use app apps.get_model to create model objects.
    """
    @property
    def app(self):
        return apps.get_containing_app_config(type(self).__module__).name

    migrate_from = None
    migrate_to = None
    django_application = None

    def setUp(self):
        assert self.migrate_from and self.migrate_to, \
            "TestCase '{}' must define migrate_from and migrate_to properties".format(type(self).__name__)
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        # Reverse to the original migration
        executor.migrate(self.migrate_from)

        self.setUpBeforeMigration(old_apps)

        # Run the migration to test
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()  # reload.
        executor.migrate(self.migrate_to)

        self.apps = executor.loader.project_state(self.migrate_to).apps

    def setUpBeforeMigration(self, apps):
        pass

    def tearDown(self):
        # Leave the db in the final state so that the test runner doesn't
        # error when truncating the database.
        # https://micknelson.wordpress.com/2013/03/01/testing-django-migrations/
        call_command('migrate', self.django_application, verbosity=0)


class DDSEndpointMigrationTestCase(TestMigrations):
    """
    Tests that DDSEndpoint is migrated from bespin to gcb-web-auth
    """


class DDSEndpointAndDDSUserCredentialDataMigrationTestCase(TestMigrations):
    """
    Tests that DukeDSSettings model is migrated to DDSEndpoint
    """
    migrate_from = '0048_auto_20180611_1534'
    migrate_to = '0049_dds_endpoint_credential_to_gcb_web_auth'
    django_application = 'data'

    def setUpBeforeMigration(self, apps):
        User = apps.get_model('auth', 'User')
        user1 = User.objects.create(username='user1')
        user2 = User.objects.create(username='user2')
        DDSEndpoint = apps.get_model('data','DDSEndpoint')
        DDSUserCredential = apps.get_model('data', 'DDSUserCredential')
        endpoint = DDSEndpoint.objects.create(
            name='endpoint1',
            agent_key='1223334444',
            api_root='https://api.example.org/api',
          )
        DDSUserCredential.objects.create(
            endpoint=endpoint,
            user=user1,
            token='token1',
            dds_id='dds_id1'
        )
        DDSUserCredential.objects.create(
            endpoint=endpoint,
            user=user2,
            token='token2',
            dds_id='dds_id2'
        )

    def test_migrates_endpoint_to_gcb_web_auth(self):
        DDSEndpoint = apps.get_model('gcb_web_auth', 'DDSEndpoint')
        endpoints = DDSEndpoint.objects.all()
        self.assertEqual(len(endpoints), 1)
        endpoint = endpoints[0]
        self.assertEqual(endpoint.name, 'endpoint1')
        self.assertEqual(endpoint.api_root, 'https://api.example.org/api')
        self.assertEqual(endpoint.agent_key, '1223334444')

    def test_migrates_credentials_to_gcb_web_auth(self):
        DDSUserCredential = apps.get_model('gcb_web_auth', 'DDSUserCredential')
        DDSEndpoint = apps.get_model('gcb_web_auth', 'DDSEndpoint')
        self.assertEqual(DDSUserCredential.objects.count(), 2)

        endpoint = DDSEndpoint.objects.first()
        credential1 = DDSUserCredential.objects.get(user__username='user1')
        self.assertEqual(credential1.token, 'token1')
        self.assertEqual(credential1.dds_id, 'dds_id1')
        self.assertEqual(credential1.endpoint, endpoint)

        credential2 = DDSUserCredential.objects.get(user__username='user2')
        self.assertEqual(credential2.token, 'token2')
        self.assertEqual(credential2.dds_id, 'dds_id2')
        self.assertEqual(credential2.endpoint, endpoint)


class JSONFieldMigrationTestCase(TestMigrations):
    migrate_from = '0058_auto_20181105_1704'
    migrate_to = '0060_remove_json_field_nullable'
    django_application = 'data'

    def setUpBeforeMigration(self, apps):
        # find models for current version of apps
        Workflow = apps.get_model('data', 'Workflow')
        WorkflowVersion = apps.get_model('data', 'WorkflowVersion')
        VMSettings = apps.get_model('data', 'VMSettings')
        VMFlavor = apps.get_model('data', 'VMFlavor')
        ShareGroup = apps.get_model('data', 'ShareGroup')
        CloudSettings = apps.get_model('data', 'CloudSettings')
        VMProject = apps.get_model('data', 'VMProject')
        VMStrategy = apps.get_model('data', 'VMStrategy')
        WorkflowConfiguration = apps.get_model('data', 'WorkflowConfiguration')

        # create data using these models
        workflow = Workflow.objects.create(name='Copy Files', tag='copyfiles')
        workflow_version1 = WorkflowVersion.objects.create(
            workflow=workflow,
            description='',
            version=1,
            url='http://someurl.com',
            fields_json='')
        WorkflowVersion.objects.create(
            workflow=workflow,
            description='',
            version=2,
            url='http://someurl.com',
            fields_json='[{"color":"red", "data": { "count": 2}}]')
        vm_flavor = VMFlavor.objects.create(name='m1.small')
        vm_project = VMProject.objects.create(name='project1')
        cloud_settings = CloudSettings.objects.create(vm_project=vm_project)
        vm_settings = VMSettings.objects.create(
            name='settings',
            cloud_settings=cloud_settings,
            image_name='someimage',
            cwl_pre_process_command='["touch", "stalefile.txt"]',
            cwl_base_command='["cwl-runner"]',
            cwl_post_process_command='["rm", "stalefile.txt"]')
        vm_strategy = VMStrategy.objects.create(
            name='large',
            vm_settings=vm_settings,
            vm_flavor=vm_flavor,
            volume_size_base=200,
            volume_size_factor=10,
            volume_mounts='{"/dev/vdb1": "/work2"}')
        share_group = ShareGroup.objects.create(name='somegroup')
        WorkflowConfiguration.objects.create(
            name='b37human',
            workflow_version=workflow_version1,
            system_job_order_json='{"color":"blue", "data": { "count": 3}}',
            default_vm_strategy=vm_strategy,
            share_group=share_group)
        WorkflowConfiguration.objects.create(
            name='b37blank',
            workflow_version=workflow_version1,
            system_job_order_json='',
            default_vm_strategy=vm_strategy,
            share_group=share_group)

    def test_migrates_workflow_version_fields(self):
        WorkflowVersion = self.apps.get_model('data', 'WorkflowVersion')
        items = WorkflowVersion.objects.order_by('version')
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].fields, [])
        self.assertEqual(len(items[1].fields), 1)
        self.assertEqual(items[1].fields[0], {'color': 'red', 'data': {'count': 2}})

    def test_migrates_workflow_configuration_fields(self):
        WorkflowConfiguration = self.apps.get_model('data', 'WorkflowConfiguration')
        items = WorkflowConfiguration.objects.order_by('name')
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].system_job_order, {})
        self.assertEqual(items[1].system_job_order, {'color': 'blue', 'data': {'count': 3}})
