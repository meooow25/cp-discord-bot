class Contest:
    __slots__ = ('name', 'site_tag', 'site_name', 'url', 'start', 'length')

    def __init__(self, name, site_tag, site_name, url, start, length):
        """Represents a competitive programming contest.

        :param name: the name of the contest
        :param site_tag: the site tag
        :param site_name: the site name
        :param url: the URL of the contest
        :param start: the timestamp of the UTC start time
        :param length: the length of the contest in seconds
        """

        self.name = name
        self.site_tag = site_tag
        self.site_name = site_name
        self.url = url
        self.start = start
        self.length = length

    def __lt__(self, other):
        return (self.start, self.length, self.site_name) < (other.start, other.length, other.site_name)

    def __repr__(self):
        return '<Contest' + str((self.name, self.site_tag, self.site_name, self.url, self.start, self.length)) + '>'


class Profile:
    __slots__ = ('handle', 'site_tag', 'site_name', 'url', 'avatar', 'name', 'rating')

    def __init__(self, handle, site_tag, site_name, url, avatar, name, rating):
        """Represents a user of a competitive programming site.

        :param handle: the user's handle
        :param site_tag: the site tag
        :param site_name: the site name
        :param url: the URL of the profile
        :param avatar: the URL of the user's avatar
        :param name: the user's full name, ``None`` if unavailable
        :param rating: the user's current rating, ``None`` if unrated
        """

        self.handle = handle
        self.site_tag = site_tag
        self.site_name = site_name
        self.url = url
        self.avatar = avatar
        self.name = name
        self.rating = rating

    def make_embed_handle_text(self):
        return f'**Handle**: [{self.handle}]({self.url})'

    def make_embed_author(self):
        """Make an author section for a Discord embed."""
        return {
            'name': f'{self.handle}',
            'url': self.url,
            'icon_url': self.avatar,
        }

    def make_embed_name_and_rating_text(self):
        """Make a formatted string containing name and rating."""
        desc = f'**Name**: {self.name}\n' if self.name is not None else ''
        desc += f'**Rating**: {self.rating if self.rating is not None else "Unrated"}'
        return desc

    def make_embed_footer(self):
        """make a footer with site name for a Discord embed."""
        return {'text': self.site_name}

    @classmethod
    def from_dict(cls, profile_dict):
        params = [profile_dict.get(key) for key in cls.__slots__]
        return Profile(*params)

    def to_dict(self):
        return {key: getattr(self, key) for key in self.__slots__}
