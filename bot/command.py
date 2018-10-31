class Command:
    """An executable bot command."""

    def __init__(self, func, name=None, usage=None, desc=None, hidden=False,
                 allow_guild=True, allow_dm=False):
        """
        :param func: the function that actually does the work
        :param name: the command name
        :param usage: command usage information
        :param desc: command description
        :param hidden: whether the command is hidden
        :param allow_guild: whether the command is allowed in guild channels
        :param allow_dm: whether the command is allowed in DM channels
        """
        self.func = func
        self.name = func.__name__ if name is None else name
        self.usage = func.__name__ if usage is None else usage
        self.desc = func.__name__ if desc is None else desc
        self.hidden = hidden
        self.allow_guild = allow_guild
        self.allow_dm = allow_dm

    async def execute(self, *args, **kwargs):
        """Execute the command."""
        await self.func(*args, **kwargs)

    def embed_field_rep(self):
        """Returns a Discord embed field representing this command."""
        return {
            'name': self.usage,
            'value': self.desc,
        }


class IncorrectUsageException(Exception):
    """Represents an exception raised when a command is used incorrectly."""

    def __init__(self, msg=None, cmd=None):
        """
        :param msg: a message to be displayed
        :param cmd: the command in context
        """
        if cmd:
            msg = f'Command "{cmd}": {msg}' if msg else f'Command "{cmd}"'
        if msg:
            super().__init__(msg)
        else:
            super().__init__()


def command(func=None, **kwargs):
    """Wraps an async function in a Command object, intended for use as a decorator"""
    if func is not None:
        return Command(func, **kwargs)
    return lambda fun: Command(fun, **kwargs)


def assert_true(val, msg=None, cmd=None):
    if val is not True:
        msg = msg or f'Expected True, found {val}'
        raise IncorrectUsageException(msg, cmd)


def assert_none(val, msg=None, cmd=None):
    if val is not None:
        msg = msg or f'Expected None, found {val}'
        raise IncorrectUsageException(msg, cmd)


def assert_not_none(val, msg=None, cmd=None):
    if val is None:
        msg = msg or f'Expected not None, found None'
        raise IncorrectUsageException(msg, cmd)


def assert_int(val, msg=None, cmd=None):
    try:
        int(val)
    except ValueError:
        msg = msg or f'Expected int, found {val}'
        raise IncorrectUsageException(msg, cmd)


def assert_arglen(args, num, msg=None, cmd=None):
    if len(args) != num:
        msg = msg or f'Expected {num} arguments, found {len(args)}'
        raise IncorrectUsageException(msg, cmd)
