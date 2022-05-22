from uuid import uuid4
from class_utils import decorate_attributes_parametrized_immutable
from functools import wraps
import itertools

class LogError(Exception):
    pass

def args_to_keys(arg, include=False, chain=True):
    if type(arg) == type(list()) or type(arg) == type(tuple()):
        l = list(map(args_to_keys, arg)) if chain else args_to_keys(arg)
    elif type(arg) == type(dict()):
        l = list(map(args_to_keys, arg.values())) \
            if chain else dict(map(lambda x: (x, args_to_keys(x, include, chain)), arg))
    else:
        try:
            return [arg._log_key] if chain else arg._log_key
        except:
            ret = None if not include else arg
            return [ret] if chain else ret
    return list(itertools.chain(*l)) if chain else l

log = []
state = {}

def _log_call(origin, call, args=[], kwargs={}, result=None, call_type='return'):
    key = origin if isinstance(origin, str) else origin._log_key
    special_keys =  ['___call']
    if key not in state and key not in special_keys: return
    entry = dict(map(lambda x: (x, state[x].__log_repr__()), state))
    affected_objects = list(
        filter(
            lambda x: x is not None and x in state, 
            args_to_keys(args) + args_to_keys(kwargs)
        )
    )
    cargs = args_to_keys(args, include=True, chain=False)
    ckwargs = args_to_keys(kwargs, include=True, chain=False)
    cresult = args_to_keys(result, include=True, chain=False)
    log.append((key, call, cargs, ckwargs, cresult, affected_objects, entry, call_type))

def _log_enter(obj):
    key = obj._log_key
    if key in state:
        raise LogError(f'log_enter failed: key {key} already taken.')
    state[key] = obj
    _log_call(obj, '___enter')

def _log_exit(obj):
    key = obj._log_key
    try:
        _log_call(obj, '___exit')
        del state[key]
    except KeyError as e:
        raise LogError(f'log_exit failed: object with key {key} doesn\'t exist.')

def get_callable_attr_decorator(instance, attr_name):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            _log_call(instance, attr_name, args, kwargs, call_type='call')
            result = f(*args, **kwargs)
            _log_call(instance, attr_name, args, kwargs, result, call_type='return')
            return result
        return wrapper
    return decorator

def logged_function(f):
    """Decorator for a function to log every call"""
    return get_callable_attr_decorator('___call', f.__name__)(f)

def log_enter(*iterable):
    for x in iterable:
        x.__enter__()

def log_exit(*iterable):
    for x in iterable:
        x.__exit__()
        

def transform_into_logger(cls, repr_fn=None, key_fn=None, excluded=[], enter_on_init=False):
    """Transforms a class into a logger that logs 
    every attribute call inside a with statement"""
    log_key_fn = key_fn if key_fn is not None else repr
    decorated_class = decorate_attributes_parametrized_immutable(
        cls,
        get_callable_attr_decorator,
        exclusion=[
            '__init__', 
            '__enter__', 
            '__exit__', 
            '__log_repr__', 
            '_log_key'
        ] + excluded
    )

    class LoggedClass(decorated_class):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            local_enter_on_init = kwargs.pop('_enter_on_init', enter_on_init)
            custom_key = kwargs.pop('_log_key', None)
            self._log_key = custom_key if custom_key is not None else log_key_fn(self)
            if enter_on_init or local_enter_on_init:
                self.__enter__()
        
        def __log_repr__(self):
            return (repr_fn if repr_fn is not None else repr)(self)

        def __enter__(self, *args, **kwargs):
            _log_enter(self)
            return self
        
        def __exit__(self, *args, **kwargs):
            _log_exit(self)
            return None
    
    return LoggedClass
