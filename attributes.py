import logging

class Property:
    def __init__(self, name, command, read_only = True):
        self._name      = name
        self._command   = command
        self._read_only = read_only

    def __get__(self, instance, owner):
        return instance._query(f"GET{self._command}")

    def __set__(self, instance, value):
        if self._read_only:
            logging.error(f"{self._name} is a read-only attribute!")
        else:
            instance._write(f"SET{self._command} {value}")

class FloatProperty(Property):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __get__(self, *args, **kwargs):
        val = super().__get__(*args, **kwargs)
        try:
            return float(val)
        except TypeError:
            logging.error(f"{self._name} TypeError : {val}")
            return None

class IntProperty(Property):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __get__(self, *args, **kwargs):
        val = super().__get__(*args, **kwargs)
        try:
            return int(val)
        except TypeError:
            logging.error(f"{self._name} TypeError : {val}")
            return None

class BoolProperty(Property):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __get__(self, *args, **kwargs):
        val = super().__get__(*args, **kwargs)
        try:
            return bool(val)
        except TypeError:
            logging.error(f"{self._name} TypeError : {val}")
            return None
    
    def __set__(self, *args, **kwargs):
        if 'value' in kwargs:
            kwargs['value'] = int(kwargs['value'])
        else:
            args = list(args)
            args[1] = int(args[1])
        super().__set__(*args, **kwargs)

class FlagProperty(Property):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __get__(self, *args, **kwargs):
        flags = super().__get__(*args, **kwargs)
        if flags:
            flags = [bool(int(f)) for f in flags.split(' ')]
            return flags
        else:
            logging.error(f"{self._name} : {flags}")
            return None

class FloatPropertyNGet(FloatProperty):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __get__(self, instance, owner):
        val = instance._query(f"{self._command}")
        try:
            return float(val)
        except TypeError:
            logging.error(f"{self._name} TypeError : {val}")
            return None