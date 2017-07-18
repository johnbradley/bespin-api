from gcb_web_auth.backends.oauth import OAuth2Backend

BESPIN_USER_GROUP = 'duke:group-manager:roles:bespin-users'


class BespinOAuth2Backend(OAuth2Backend):
    """
    Adds check to make sure users belong to the bespin-user group manager group.
    This group is managed via https://groups.oit.duke.edu/groupmanager/.
    """
    def check_user_details(self, details):
        duke_unique_id = details['dukeUniqueID']
        self.verify_user_belongs_to_group(duke_unique_id, BESPIN_USER_GROUP)
