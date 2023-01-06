from typing import Optional, List


class Property:
    def __init__(
        self,
        name: str,
        command: str,
        read_prefix: str = "GET",
        write_prefix: str = "SET",
        write_command: Optional[str] = None,
        read_only: bool = True,
    ):
        self._name = name
        self._command = command
        self._read_only = read_only
        self._read_prefix = read_prefix
        self._write_prefix = write_prefix
        self._write_command = write_command

    def __get__(self, instance, owner):
        return instance._query(f"{self._read_prefix}{self._command}")

    def __set__(self, instance, value) -> None:
        if self._read_only:
            raise ValueError(f"{self._name} is a read-only attribute")
        else:
            if self._write_command is None:
                instance._write(f"{self._write_prefix}{self._command} {value}")
            else:
                instance._write(f"{self._write_prefix}{self._write_command} {value}")


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

    def __get__(self, *args, **kwargs) -> List[bool]:
        ret = super().__get__(*args, **kwargs)
        flags = [bool(int(f)) for f in ret.split(" ")]
        return flags
