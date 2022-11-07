from typing import Optional


class Property:
    def __init__(self, name: str, command: str, read_only: bool = True):
        self._name = name
        self._command = command
        self._read_only = read_only

    def __get__(self, instance, owner):
        return instance._query(f"GET{self._command}")

    def __set__(self, instance, value) -> None:
        if self._read_only:
            raise ValueError(f"{self._name} is a read-only attribute")
        else:
            instance._write(f"SET{self._command} {value}")


class FloatProperty(Property):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __get__(self, *args, **kwargs) -> Optional[float]:
        val = super().__get__(*args, **kwargs)
        return float(val)


class IntProperty(Property):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __get__(self, *args, **kwargs) -> Optional[int]:
        val = super().__get__(*args, **kwargs)
        return int(val)


class BoolProperty(Property):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __get__(self, *args, **kwargs) -> Optional[bool]:
        val = super().__get__(*args, **kwargs)
        return bool(val)

    def __set__(self, *args, **kwargs):
        if "value" in kwargs:
            kwargs["value"] = int(kwargs["value"])
        else:
            args = list(args)
            args[1] = int(args[1])
        super().__set__(*args, **kwargs)


class FlagProperty(Property):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __get__(self, *args, **kwargs) -> list[bool]:
        ret = super().__get__(*args, **kwargs)
        flags = [bool(int(f)) for f in ret.split(" ")]
        return flags


class FloatPropertyNGet(FloatProperty):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __get__(self, instance, owner):
        val = instance._query(f"{self._command}")
        return float(val)
