
class Contest:
    def __init__(self, name, site, url, start, length):
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
