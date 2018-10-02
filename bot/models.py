from sites.models import Profile


class User:

    def __init__(self, discord_id, dm_channel_id, site_profiles=None):
        self.discord_id = discord_id
        self.dm_channel_id = dm_channel_id
        if site_profiles is None:
            site_profiles = []
        self.site_profiles = site_profiles
        self._profile_map = {profile.site_tag: profile for profile in self.site_profiles}

    def update_profile(self, profile):
        old_profile = self._profile_map.get(profile.site_tag)
        self._profile_map[profile.site_tag] = profile
        self.site_profiles = list(self._profile_map.values())
        return old_profile is None or old_profile.to_dict() != profile.to_dict()

    def delete_profile(self, site_tag):
        profile = self._profile_map.get(site_tag)
        if profile is None:
            return False
        del self._profile_map[site_tag]
        self.site_profiles = list(self._profile_map.values())
        return True

    def get_profile_for_site(self, site_tag):
        return self._profile_map.get(site_tag)

    @classmethod
    def from_dict(cls, user_d):
        return cls(
            user_d['discord_id'],
            user_d['dm_channel_id'],
            [Profile.from_dict(profile_dict) for profile_dict in user_d['site_profiles']]
        )

    def to_dict(self):
        return {
            'discord_id': self.discord_id,
            'dm_channel_id': self.dm_channel_id,
            'site_profiles': [profile.to_dict() for profile in self.site_profiles]
        }
