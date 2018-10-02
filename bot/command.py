class Command:
    class IncorrectUsageException(Exception):
        pass

    def __init__(self, func, name=None, usage=None, desc=None, experimental=False):
        self.func = func
        self.name = func.__name__ if name is None else name
        self.usage = func.__name__ if usage is None else usage
        self.desc = func.__name__ if desc is None else desc
        self.experimental = experimental

    async def execute(self, *args, **kwargs):
        await self.func(*args, **kwargs)


def command(func=None, **kwargs):
    """Wraps a function in a Command object, intended for use as a decorator"""
    if func is not None:
        return Command(func, **kwargs)
    return lambda fun: Command(fun, **kwargs)


def assert_true(arg):
    if not arg:
        raise Command.IncorrectUsageException()


def assert_arglen(args, num):
    if len(args) != num:
        raise Command.IncorrectUsageException()
