from functools import wraps

def receiver(signal, **kwargs):
    '''
    A decorator for connecting receivers to signals. Used by passing in the
    signal and keyword arguments to connect::

    >>> @receiver(post_save, sender=MyModel)
    ... def signal_receiver(sender, **kwargs):
    ...     ...

    '''

    def decorated(func):
        signal.connect(func, **kwargs)
    return decorated

