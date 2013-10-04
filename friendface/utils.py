class memoize(object):
    """
    Memoize the result of a property call.

    >>> class A(object):
    >>>     @memoize
    >>>     def func(self):
    >>>         return 'foo'
    """

    def __init__(self, func):
        self.__name__ = func.__name__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__
        self.func = func

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        d, n = vars(obj), self.__name__
        if n not in d:
            value = self.func(obj)
            d[n] = value
        return value


# Support for Django 1.4 User models.
def get_user_model():
    try:
        from django.contrib.auth import get_user_model
        return get_user_model()
    except ImportError:
        from django.contrib.auth.models import User
        return User
