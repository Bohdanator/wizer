def decorate_attributes_parametrized_immutable(
    cls, 
    get_callables_decorator=None, 
    get_non_callables_decorator=None, 
    exclusion=[]
):
    """
    Decorates callable and non-callable attributes of a class.
    The decorators are obtained by calling get_<decorator> with
    arguments <instance>, <attribute name> respectively.
    """
    exclusion_function = exclusion \
        if callable(exclusion) else lambda x: x in exclusion
    class DecoratedClass(cls):
        def __getattribute__(self, __name: str):
            val = cls.__getattribute__(self, __name)
            if exclusion_function(__name):
                return val
            if callable(val) and get_callables_decorator is not None:
                return get_callables_decorator(self, __name)(val)
            if get_non_callables_decorator is not None:
                return get_non_callables_decorator(self, __name)(val)
            return val

    DecoratedClass.__name__ = cls.__name__
    # TODO other properties
    return DecoratedClass         

def decorate_attributes_immutable(
    cls, 
    callables_decorator=None, 
    non_callables_decorator=None, 
    exclusion=[]
):
    return decorate_attributes_parametrized_immutable(
        cls,
        (lambda instance, attr: callables_decorator) \
            if callables_decorator is not None else None,
        (lambda instance, attr: non_callables_decorator) \
            if non_callables_decorator is not None else None,
        exclusion,
    )

def decorate_attributes_parametrized(
    cls,
    get_callables_decorator=None,
    get_non_callables_decorator=None,
    exclusion=[],
):
    """
    Decorates callable and non-callable attributes of a class.
    The decorators are obtained by calling get_<decorator> with
    arguments <instance>, <attribute name> respectively.
    """
    exclusion_function = exclusion if callable(exclusion) else lambda x: x in exclusion
    def __modified_getattribute__(self, __name):
        val = cls.__original_getattribute__(self, __name)
        if exclusion_function(__name):
            return val
        if callable(val) and get_callables_decorator is not None:
            return get_callables_decorator(self, __name)(val)
        if get_non_callables_decorator is not None:
            return get_non_callables_decorator(self, __name)(val)
        return val
    setattr(cls, '__original_getattribute__', cls.__getattribute__)
    setattr(cls, '__getattribute__', __modified_getattribute__)
    return cls

def decorate_attributes(
    cls, 
    callables_decorator=None, 
    non_callables_decorator=None, 
    exclusion=[]
):
    return decorate_attributes_parametrized(
        cls,
        (lambda instance, attr: callables_decorator) \
            if callables_decorator is not None else None,
        (lambda instance, attr: non_callables_decorator) \
            if non_callables_decorator is not None else None,
        exclusion,
    )

def decorate_methods_parametrized(cls, get_decorator, exclusion=[]):
    exclusion_function = \
        exclusion if callable(exclusion) else lambda x: x in exclusion
    excl = ['__class__', '__repr__', '__new__']
    for attr_name in dir(cls):
        if attr_name not in excl and not exclusion_function(attr_name):
            attr = getattr(cls, attr_name)
            if callable(attr):
                setattr(cls, attr_name, get_decorator(attr_name)(attr))
    return cls

def decorate_methods(cls, decorator, exclusion=[]):
    return decorate_methods_parametrized(cls, lambda attr: decorator, exclusion)