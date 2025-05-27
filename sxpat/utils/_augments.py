from typing import Iterable

import time
import functools as ft

def augment(extra_parameters: Iterable[str]):
    """
        Applies augmentations to the function.  
        The augmented function will return a tuple containing the original function result, followed by the wanted augmentations in the passed order.

        Available augmentations:
            - "timed": measure the elapsed time from the start to the end of the function.
    """

    def do_timed(function):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = function(*args, **kwargs)
            total_time = time.time() - start_time
            return result, total_time
        return wrapper

    def unpacker(function, depth: int):
        def wrapper(*args, **kwargs):
            result = function(*args, **kwargs)
            other_results = []
            for _ in range(depth):
                result, other = result
                other_results.append(other)
            return result, *reversed(other_results)
        return wrapper

    decorators = {
        "timed": do_timed
    }

    def decorator(function):
        wrapper = function
        for key in extra_parameters: wrapper = decorators[key](wrapper)
        return unpacker(wrapper, len(extra_parameters))

    return decorator


def static(**vars):
    def decorate(func):
        for (k, v) in vars.items(): setattr(func, k, v)
        return func
    return decorate


def cached(func):
    """This decorator caches all results of the function, so that repeated calls do not run the computation again."""
    return ft.wraps(func)(ft.lru_cache(maxsize=None)(func))
