import concurrent.futures as _futures

import time as _time
import weakref as _weakref
import itertools as _itertools
import collections as _collections


class ThreadPoolExecutor(_futures.ThreadPoolExecutor):
    def map_unordered(self, fn, *iterables, timeout=None, chunksize=1, buffersize=None):
        """
        Returns an iterator similar to map(fn, iter) but values get yielded as
        soon as they are available.

        Args:
            fn: A callable that will take as many arguments as there are
                passed iterables.
            timeout: The maximum number of seconds to wait. If None, then there
                is no limit on the wait time.
            chunksize: The size of the chunks the iterable will be broken into
                before being passed to a child process. This argument is only
                used by ProcessPoolExecutor; it is ignored by
                ThreadPoolExecutor.
            buffersize: The number of submitted tasks whose results have not
                yet been yielded. If the buffer is full, iteration over the
                iterables pauses until a result is yielded from the buffer.
                If None, all input elements are eagerly collected, and a task is
                submitted for each.

        Returns:
            An iterator equivalent to: map(func, *iterables) but the result may
            be out-of-order.

        Raises:
            TimeoutError: If the entire result iterator could not be generated
                before the given timeout.
            Exception: If fn(*args) raises for any values.
        
        Authors:
            Marco Biasion
            Python: This function has been assembled using the implementation of `as_completed` and `Executor.map`.
        """

        if buffersize is not None and not isinstance(buffersize, int):
            raise TypeError("buffersize must be an integer or None")
        if buffersize is not None and buffersize < 1:
            raise ValueError("buffersize must be None or > 0")

        if timeout is not None:
            end_time = timeout + _time.monotonic()

        zipped_iterables = zip(*iterables)
        if buffersize:
            fs = _collections.deque(
                self.submit(fn, *args)
                for args in _itertools.islice(zipped_iterables, buffersize)
            )
        else:
            fs = _collections.deque(
                self.submit(fn, *args)
                for args in zipped_iterables
            )

        # Use a weak reference to ensure that the executor can be garbage
        # collected independently of the result_iterator closure.
        executor_weakref = _weakref.ref(self)

        # Yield must be hidden in closure so that the futures are submitted
        # before the first iterator value is required.
        def result_iterator():
            try:
                while fs:
                    if timeout is None:
                        wait_timeout = None
                    else:
                        wait_timeout = end_time - _time.monotonic()
                        if wait_timeout < 0: raise TimeoutError()

                    # Careful not to keep a reference to the futures
                    done = _futures.wait(
                        fs,
                        timeout=wait_timeout,
                        return_when=_futures.FIRST_COMPLETED
                    ).done

                    if (
                        buffersize
                        and (ex := executor_weakref())
                    ):
                        while len(fs) < buffersize:
                            if (args := next(zipped_iterables, None)):
                                fs.append(ex.submit(fn, *args))

                    # Careful not to keep a reference to the futures
                    while done:
                        fs.remove(future := done.pop())
                        result = future.result()
                        del future
                        yield result

            finally:
                for future in fs:
                    future.cancel()

        return result_iterator()
