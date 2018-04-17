from gcb_web_auth.backends.oauth import OAuth2Backend
from django.conf import settings


class BespinOAuth2Backend(OAuth2Backend):
    """
    If required by settings, checks that user belongs to group-manager group
    """
    def check_user_details(self, details):
        if settings.REQUIRED_GROUP_MANAGER_GROUP:
            duke_unique_id = details['dukeUniqueID']
            self.verify_user_belongs_to_group(duke_unique_id, settings.REQUIRED_GROUP_MANAGER_GROUP)
