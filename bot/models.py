from sites.models import Profile


class User:

    def __init__(self, discord_id, site_profiles=None):
        self.discord_id = discord_id
        if site_profiles is None:
            site_profiles = []
        self.site_profiles = site_profiles

    @classmethod
    def from_dict(cls, user_dict):
        return User(
            user_dict['discord_id'],
            [Profile.from_dict(profile_dict) for profile_dict in user_dict['site_profiles']]
        )

    def to_dict(self):
        return {
            'discord_id': self.discord_id,
            'site_profiles': [profile.to_dict() for profile in self.site_profiles]
        }
