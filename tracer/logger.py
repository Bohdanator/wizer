from uuid import uuid4
from classutils.decorators import (
    decorate_attributes_parametrized_immutable,
    decorate_attributes_parametrized,
)
from functools import wraps
import itertools

class LogError(Exception):
    pass

def args_to_keys(arg, include=False, chain=True):
    if type(arg) == type(list()) or type(arg) == type(tuple()):
        l = list(map(lambda x: args_to_keys(x, include, chain), arg))
    elif type(arg) == type(dict()):
        l = list(map(args_to_keys, arg.values())) \
            if chain else dict(map(lambda x: (x, args_to_keys(x, include, chain)), arg))
    else:
        try:
            return [arg.__log_key__()] if chain else arg.__log_key__()
        except:
            ret = None if not include else arg
            return [ret] if chain else ret
    return list(itertools.chain(*l)) if chain else l

log = []
state = {}

def _log_call(origin, call, args=[], kwargs={}, result=None, call_type='return'):
    key = origin if isinstance(origin, str) else origin.__log_key__()
    special_keys =  ['___call']
    if key not in state and key not in special_keys: return
    entry = dict(map(lambda x: (x, state[x].__log_repr__()), state))
    affected_objects = list(
        filter(
            lambda x: x is not None and x in state.keys(), 
            args_to_keys(args) + args_to_keys(kwargs)
        )
    )
    cargs = args_to_keys(args, include=True, chain=False)
    ckwargs = args_to_keys(kwargs, include=True, chain=False)
    cresult = args_to_keys(result, include=True, chain=False)
    log.append((key, call, cargs, ckwargs, cresult, affected_objects, entry, call_type))

def _log_enter(obj):
    key = obj.__log_key__()
    if key in state:
        return #raise LogError(f'log_enter failed: key {key} already taken.')
    state[key] = obj
    _log_call(obj, '___enter')

def _log_exit(obj):
    key = obj.__log_key__()
    try:
        _log_call(obj, '___exit')
        del state[key]
    except KeyError as e:
        return #raise LogError(f'log_exit failed: object with key {key} doesn\'t exist.')

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
    "Add objects to the log state"
    for x in iterable:
        x.__enter__()

def log_exit(*iterable):
    "Remove objects from the log state"
    for x in iterable:
        x.__exit__()

def transform_into_logger(cls, repr_fn=None, key_fn=None, excluded=[], enter_on_init=False):
    """Transforms a class into a logger that logs 
    every attribute call inside a with statement"""
    log_key_fn = key_fn if key_fn is not None else str
    log_repr_fn = repr_fn if repr_fn is not None else repr

    def _log_repr(self):
        return log_repr_fn(self)
    
    def _log_key(self):
        if hasattr(self, '_log_key'):
            return self._log_key
        else:
            self._log_key = log_key_fn(self)
            return self._log_key
    
    def _enter(self):
        _log_enter(self)
        return self
    
    def _exit(self):
        _log_exit(self)
        return None
    
    # we can do this, because __new__ is implicitly static
    original_new = cls.__new__
    def _new(new_cls, *args, **kwargs):
        instance = original_new(new_cls, *args, **kwargs)
        if enter_on_init:
            instance.__enter__()
        return instance
    
    excl = excluded + [
        '__log_repr__',
        '__log_key__',
        '__enter__',
        '__exit__',
        '__class__',
        '__new__',
        '__init__',
    ]
    decorate_attributes_parametrized(cls, get_callable_attr_decorator, exclusion=excl)
    setattr(cls, '__new__', _new)
    setattr(cls, '__log_repr__', _log_repr)
    setattr(cls, '__log_key__', _log_key)
    setattr(cls, '__enter__', _enter)
    setattr(cls, '__exit__', _exit)    
    return cls 

def create_logger_from(cls, repr_fn=None, key_fn=None, excluded=[], enter_on_init=False):
    log_key_fn = key_fn if key_fn is not None else str
    log_repr_fn = repr_fn if repr_fn is not None else repr
    excl = excluded + [
        '__log_repr__',
        '__log_key__',
        '__enter__',
        '__exit__',
        '__class__',
        '__new__',
        '__init__',
    ]

    def _log_repr(self):
        return log_repr_fn(self)
    
    def _log_key(self):
        if hasattr(self, '_log_key'):
            return self._log_key
        else:
            self._log_key = log_key_fn(self)
            return self._log_key
    
    def _enter(self):
        _log_enter(self)
        return self
    
    def _exit(self):
        _log_exit(self)
        return None

    class LoggedClass(cls):
        def __new__(cls, *args, **kwargs):
            instance = super().__new__(cls, *args, **kwargs)
            setattr(instance, '__class__', decorate_attributes_parametrized_immutable(instance.__class__, get_callable_attr_decorator, exclusion=excl))
            setattr(instance.__class__, '__log_repr__', _log_repr)
            setattr(instance.__class__, '__log_key__', _log_key)
            setattr(instance.__class__, '__enter__', _enter)
            setattr(instance.__class__, '__exit__', _exit)   
            if enter_on_init:
                instance.__enter__()
            return instance

    return LoggedClass #decorate_attributes_parametrized(LoggedClass, get_callable_attr_decorator, exclusion=excl) 

def logged_class(repr_fn=None, key_fn=None, excluded=[], enter_on_init=False):
    def decorator(cls):
        return transform_into_logger(cls, repr_fn, key_fn, excluded, enter_on_init)
    return decorator