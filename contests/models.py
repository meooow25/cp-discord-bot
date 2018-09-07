class Contest:

    def __init__(self, name, site, url, start, length):
        """
        :param name: the name of the contest
        :param site: the site of the contest
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

    __str__ = __repr__
