class MPBCommandError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MPBKeyError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("Put key into enable position.")
