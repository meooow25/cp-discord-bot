class Contest:
    __slots__ = ('name', 'site', 'url', 'start', 'length')

    def __init__(self, name, site, url, start, length):
        """
        Represents a competitive programming contest.

        :param name: the name of the contest
        :param site: the site name
        :param url: the URL of the contest
        :param start: the timestamp of the UTC start time
        :param length: the length of the contest in seconds
        """

        self.name = name
        self.site = site
        self.url = url
        self.start = start
        self.length = length

    def __lt__(self, other):
        return (self.start, self.length, self.site) < (other.start, other.length, other.site)

    def __repr__(self):
        return 'Contest' + str((self.name, self.site, self.url, self.start, self.length))


class Profile:
    __slots__ = ('handle', 'site', 'name', 'rating')

    def __init__(self, handle, site, name, rating):
        """
        Represents a user of a competitive programming site.

        :param handle: the user's handle
        :param site: the site name
        :param name: the user's full name, ``None`` if unavailable
        :param rating: the user's current rating, ``None`` if unrated
        """

        self.handle = handle
        self.site = site
        self.name = name
        self.rating = rating

    @classmethod
    def from_dict(cls, profile_dict):
        return Profile(
            profile_dict['handle'],
            profile_dict['site'],
            profile_dict.get('name'),
            profile_dict.get('rating')
        )

    def to_dict(self):
        return {key: getattr(self, key) for key in self.__slots__}
