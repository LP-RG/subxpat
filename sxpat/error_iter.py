from typing import Protocol as _Protocol
import abc as _abc

import math as _math


class ErrorIterator(_Protocol):
    _max_error: int
    _error_to_origin: int = 0
    _error_to_previous: int = 0

    def __init__(self, max_error: int):
        self._max_error = max_error

    def __iter__(self): return self

    @_abc.abstractmethod
    def get_next(self) -> int | None: ...

    def give_feedback(self, error_to_origin: int | None = None, error_to_previous: int | None = None):
        if error_to_origin is not None: self._error_to_origin = error_to_origin
        if error_to_previous is not None: self._error_to_previous = error_to_previous

    def __next__(self) -> int:
        _next = self.get_next()
        if _next is None: raise StopIteration()
        return _next


class XPATEI(ErrorIterator):
    def __init__(self, max_error: int):
        super().__init__(max_error)
        self._done = False

    def get_next(self) -> int | None:
        if self._done:
            return None
        else:
            self._done = True
            return self._max_error


class DescendingEI(ErrorIterator):
    def __init__(self, max_error: int):
        super().__init__(max_error)
        self._iteration: int = 0
        self._log2 = int(_math.log2(max_error))

    def get_next(self) -> int | None:
        self._iteration += 1
        err = int(2 ** (self._log2 - self._iteration))
        if err > 0:
            return err
        else:
            return None


class SmartDescendingEI(ErrorIterator):
    def __init__(self, max_error: int):
        super().__init__(max_error)
        self._error: int = -1

    def get_next(self) -> int | None:
        if self._error == -1:
            self._error = self._max_error
        elif self._error_to_previous == 0:
            if self._error == 1:
                self._error = 0
            else:
                if self._error % 2 == 1: self._error += 1
                self._error = self._error // 2

        if self._error > 0:
            return self._error
        else:
            return None


class AscendingEI(ErrorIterator):
    def __init__(self, max_error: int, persistance_limit: int):
        super().__init__(max_error)
        #
        self._persistence_limit = persistance_limit
        self._persistence: int = 0
        #
        step = max(max_error // 8, 1)
        self._thresholds = list(range(step, max_error + step, step))
        self._index: int = -1

    def get_next(self) -> int | None:
        if (
            self._persistence == self._persistence_limit
            or self._error_to_previous == 0
        ):
            self._persistence = 0
            self._index += 1
        else:
            self._persistence += 1

        if self._index < len(self._thresholds):
            return self._thresholds[self._index]
        else:
            return None


class SmartAscendingEI(ErrorIterator):
    def __init__(self, max_error: int, persistence_limit: int):
        super().__init__(max_error)
        self._error: int = 0
        #
        self._persistence_limit = persistence_limit
        self._persistence: int = 0

    def get_next(self) -> int | None:
        if self._error == 0:
            self._error = 1
        elif (
            self._persistence == self._persistence_limit
            or self._error_to_previous == 0
        ):
            self._persistence = 0
            self._error *= 2
        else:
            self._persistence += 1

        if self._error <= self._max_error:
            return self._error
        else:
            return None
