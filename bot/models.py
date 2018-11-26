from .sites import Profile


class User:
    """A user of the bot.

    Has attributes related to Discord and CP sites.
    """

    def __init__(self, discord_id, dm_channel_id, site_profiles=None):
        self.discord_id = discord_id
        self.dm_channel_id = dm_channel_id
        if site_profiles is None:
            site_profiles = []
        self.site_profiles = site_profiles
        self._profile_map = {profile.site_tag: profile for profile in self.site_profiles}

    def update_profile(self, profile):
        """Update or create the user's site profile.

         Returns ``True`` if the profile was created or updated, ``False`` if the profile was not changed.
         """
        old_profile = self._profile_map.get(profile.site_tag)
        self._profile_map[profile.site_tag] = profile
        self.site_profiles = list(self._profile_map.values())
        if old_profile is None:
            changed_any = changed_name_or_rating = True
        else:
            changed_any = old_profile.to_dict() != profile.to_dict()
            changed_name_or_rating = (old_profile.name, old_profile.rating) != (profile.name, profile.rating)
        return changed_any, changed_name_or_rating

    def delete_profile(self, site_tag):
        """Delete the user's profile aasociated with the given site tag.

        Returns ``True`` if the profile was found and deleted, ``False`` if the profile did not exist.
        """
        profile = self._profile_map.get(site_tag)
        if profile is None:
            return False
        del self._profile_map[site_tag]
        self.site_profiles = list(self._profile_map.values())
        return True

    def get_profile_for_site(self, site_tag):
        """Returns the site profile of the user for the given site tag, ``None`` if no such profile exists."""
        return self._profile_map.get(site_tag)

    def get_profile_embed(self, site_tag):
        profile = self.get_profile_for_site(site_tag)
        if profile is None:
            return None
        return {
            'author': profile.make_embed_author(),
            'description': profile.make_embed_name_and_rating_text(),
            'footer': profile.make_embed_footer(),
        }

    @staticmethod
    def get_profile_change_embed(old_profile, new_profile):
        return {
            'author': new_profile.make_embed_author(),
            'fields': [
                {
                    'name': 'Previous',
                    'value': old_profile.make_embed_name_and_rating_text(),
                    'inline': 'true',
                },
                {
                    'name': 'Current',
                    'value': new_profile.make_embed_name_and_rating_text(),
                    'inline': 'true',
                },
            ],
            'footer': new_profile.make_embed_footer(),
        }

    def get_all_profiles_embed(self):
        if not self.site_profiles:
            return None
        self.site_profiles.sort(key=lambda profile: profile.site_name)
        fields = []
        for profile in self.site_profiles:
            field = {
                'name': profile.site_name,
                'value': profile.make_embed_handle_text() + '\n'
                         + profile.make_embed_name_and_rating_text(),
                'inline': True,
            }
            fields.append(field)
        return {'fields': fields}

    @classmethod
    def from_dict(cls, user_d):
        """Creates and returns a user object from its ``dict`` representation."""
        return cls(
            user_d['discord_id'],
            user_d['dm_channel_id'],
            [Profile.from_dict(profile_dict) for profile_dict in user_d['site_profiles']]
        )

    def to_dict(self):
        """Returns a ``dict`` representing the user."""
        return {
            'discord_id': self.discord_id,
            'dm_channel_id': self.dm_channel_id,
            'site_profiles': [profile.to_dict() for profile in self.site_profiles]
        }
