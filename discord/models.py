from enum import IntEnum


class User:
    __slots__ = ('id', 'username', 'discriminator', 'bot')

    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.username = kwargs['username']
        self.discriminator = kwargs['discriminator']
        self.bot = kwargs.get('bot')

    def to_dict(self):
        return {
            key: getattr(self, key)
            for key in self.__slots__
            if getattr(self, key) is not None
        }


class Channel:
    __slots__ = ('id', 'type', 'name', 'guild_id', 'recipients')

    class Type(IntEnum):
        GUILD_TEXT = 0
        DM = 1
        GUILD_VOICE = 2
        GROUP_DM = 3
        GUILD_CATEGORY = 4

    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.type = self.Type(kwargs['type'])
        self.name = kwargs.get('name')
        self.guild_id = kwargs.get('guild_id')
        self.recipients = None
        if kwargs.get('recipients'):
            self.recipients = [User(**user_d) for user_d in kwargs.get('recipients')]

    def to_dict(self):
        channel_d = {
            key: getattr(self, key)
            for key in self.__slots__
            if getattr(self, key) is not None
        }
        if self.recipients:
            channel_d['recipients'] = [user.to_dict() for user in self.recipients]
        return channel_d


class Message:
    __slots__ = ('id', 'type', 'channel_id', 'webhook_id', 'author', 'content', 'embeds')

    class Type(IntEnum):
        DEFAULT = 0
        RECIPIENT_ADD = 1
        RECIPIENT_REMOVE = 2
        CALL = 3
        CHANNEL_NAME_CHANGE = 4
        CHANNEL_ICON_CHANGE = 5
        CHANNEL_PINNED_MESSAGE = 6
        GUILD_MEMBER_JOIN = 7

    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.type = self.Type(kwargs['type'])
        self.channel_id = kwargs['channel_id']
        self.webhook_id = kwargs.get('webhook_id')
        self.author = User(**kwargs['author']) if not self.webhook_id else None
        self.content = kwargs['content']
        self.embeds = kwargs['embeds']
