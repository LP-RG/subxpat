class ImportTimer:
    def __init__(self):
        self.time = 0

    def _instrument(self):
        from time import perf_counter
        import builtins

        __builtin_import__ = builtins.__import__  # store a reference to the built-in import

        def __custom_import__(name, *args, **kwargs):
            _time = perf_counter()
            ret = __builtin_import__(name, *args, **kwargs)
            self.time += perf_counter() - _time

            return ret  # return back the actual import result

        builtins.__import__ = __custom_import__  # override the built-in import with our method

    @classmethod
    def instrument(cls):
        timer = cls()
        timer._instrument()
        return timer
