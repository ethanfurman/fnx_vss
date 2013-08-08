class LazyAttr(object):
    "doesn't create object until actually accessed"
    def __init__(yo, func=None, doc=None):
        yo.fget = func
        yo.__doc__ = doc or func.__doc__
    def __call__(yo, func):
        yo.fget = func
    def __get__(yo, instance, owner):
        if instance is None:
            return yo
        return yo.fget(instance)
class Missing(object):
    "if object hasn't been created, raise AttributeError"
    def __init__(yo, func=None, doc=None):
        yo.fget = func
        yo.__doc__ = doc or func.__doc__
    def __call__(yo, func):
        yo.fget = func
    def __get__(yo, instance, owner):
        if instance is None:
            return yo.fget(instance)
        raise AttributeError("%s must be added to this %s instance for full functionality" % (yo.fget.__name__, owner.__name__))
