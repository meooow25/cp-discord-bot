class Channel:
    TYPE_GUILD_TEXT = 0
    TYPE_DM = 1
    TYPE_GUILD_VOICE = 2
    TYPE_GROUP_DM = 3
    TYPE_GUILD_CATEGORY = 4

    def __init__(self, id, type):
        self.id = id
        self.type = type

    @classmethod
    def from_dict(cls, channel_dict):
        if channel_dict['type'] == cls.TYPE_GUILD_TEXT:
            return GuildTextChannel(channel_dict['id'], channel_dict.get('name', ''))
        if channel_dict['type'] == cls.TYPE_DM:
            return DMChannel(channel_dict['id'], channel_dict['recipients'])
        return Channel(channel_dict['id'], channel_dict['type'])

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
        }


class GuildTextChannel(Channel):
    def __init__(self, id, name):
        super().__init__(id, Channel.TYPE_GUILD_TEXT)
        self.name = name

    def to_dict(self):
        """Overrides to_dict in Channel"""
        d = super().to_dict()
        d['name'] = self.name
        return d


class DMChannel(Channel):
    def __init__(self, id, recipients):
        super().__init__(id, Channel.TYPE_DM)
        self.recipients = recipients

    def to_dict(self):
        """Overrides to_dict in Channel"""
        d = super().to_dict()
        d['recipients'] = self.recipients
        return d


class User:

    def __init__(self, id):
        self.id = id

    def to_dict(self):
        return {'id': self.id}
