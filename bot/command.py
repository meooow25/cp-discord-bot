class Command:
    """An executable bot command."""

    class IncorrectUsageException(Exception):
        pass

    def __init__(self, func, name=None, usage=None, desc=None, hidden=False):
        """
        :param func: the function that actually does the work
        :param name: the command name
        :param usage: command usage information
        :param desc: command description
        :param hidden: whether the command is hidden
        """
        self.func = func
        self.name = func.__name__ if name is None else name
        self.usage = func.__name__ if usage is None else usage
        self.desc = func.__name__ if desc is None else desc
        self.experimental = hidden

    async def execute(self, *args, **kwargs):
        """Execute the command."""
        await self.func(*args, **kwargs)

    @staticmethod
    def assert_true(arg, msg=None):
        if arg is not True:
            msg = msg or f'Expected True, found {arg}'
            raise Command.IncorrectUsageException(msg)

    @staticmethod
    def assert_none(arg, msg=None):
        if arg is not None:
            msg = msg or f'Expected None, found {arg}'
            raise Command.IncorrectUsageException(msg)

    @staticmethod
    def assert_not_none(arg, msg=None):
        if arg is None:
            msg = msg or f'Expected not None, found None'
            raise Command.IncorrectUsageException(msg)

    @staticmethod
    def assert_arglen(args, num, msg=None):
        if len(args) != num:
            msg = msg or f'Expected {num} arguments, found {len(args)} in command: {args}'
            raise Command.IncorrectUsageException(msg)


def command(func=None, **kwargs):
    """Wraps an async function in a Command object, intended for use as a decorator"""
    if func is not None:
        return Command(func, **kwargs)
    return lambda fun: Command(fun, **kwargs)
