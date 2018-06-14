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



