from django.core.management.base import BaseCommand, CommandError
from data.models import ShareGroup, DDSUser
from data.importers import BaseCreator


class ShareGroupCreator(BaseCreator):

    def create_share_group(self, group_name):
        share_group, created = ShareGroup.objects.get_or_create(name=group_name)
        self.log_creation(created, 'ShareGroup', group_name, share_group.id)
        return share_group

    def create_dds_user(self, name, dds_id):
        dds_user, created = DDSUser.objects.get_or_create(name=name, dds_id=dds_id)
        self.log_creation(created, 'DDSUser', name, dds_user.id)
        return dds_user

    def add_dds_user_to_share_group(self, dds_user, share_group):
        share_group.users.add(dds_user)
        self.log('Added {} to share group {}'.format(dds_user, share_group))


class Command(BaseCommand):
    help = """Creates share groups with specified dds users"""

    def __init__(self):
        super(Command, self).__init__()
        self.creator = ShareGroupCreator(self.stdout, self.stderr)

    def add_arguments(self, parser):
        parser.add_argument('group_name', help='Name of the share group to create')
        parser.add_argument('--usernames', help='User to add to share group', nargs='*')
        parser.add_argument('--dds_ids', help='DukeDS UUID of user', nargs='*')

    def handle(self, **options):
        group_name = options['group_name']
        usernames = options['usernames'] or []
        dds_ids = options['dds_ids'] or []

        if not len(usernames) == len(dds_ids):
            raise CommandError('usernames and dds_ids must be equal length')

        share_group = self.creator.create_share_group(group_name)

        for username, dds_id in zip(usernames, dds_ids):
            dds_user = self.creator.create_dds_user(username, dds_id)
            self.creator.add_dds_user_to_share_group(dds_user, share_group)

