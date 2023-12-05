import time
from typing import Any, Callable, Iterable
import colorama


class color:
    def factory(color: str) -> Callable[[str], str]:
        return lambda s: color + s + colorama.Fore.RESET

    s = success = green = staticmethod(factory(colorama.Fore.GREEN))
    w = warning = yellow = staticmethod(factory(colorama.Fore.YELLOW))
    e = error = red = staticmethod(factory(colorama.Fore.RED))
    i1 = info1 = cyan = staticmethod(factory(colorama.Fore.CYAN))
    i2 = info2 = blue = staticmethod(factory(colorama.Fore.BLUE))
    i3 = info3 = magenta = staticmethod(factory(colorama.Fore.MAGENTA))
    black = staticmethod(factory(colorama.Fore.BLACK))
    white = staticmethod(factory(colorama.Fore.WHITE))


class pprint:
    def factory(color: str):
        def p(title: Any, *args: Any, **kwargs: Any) -> None:
            print(color + str(title) + colorama.Fore.RESET, *args, **kwargs)
        return p

    s = success = green = staticmethod(factory(colorama.Fore.GREEN))
    w = warning = yellow = staticmethod(factory(colorama.Fore.YELLOW))
    e = error = red = staticmethod(factory(colorama.Fore.RED))
    i1 = info1 = cyan = staticmethod(factory(colorama.Fore.CYAN))
    i2 = info2 = blue = staticmethod(factory(colorama.Fore.BLUE))
    i3 = info3 = magenta = staticmethod(factory(colorama.Fore.MAGENTA))
    black = staticmethod(factory(colorama.Fore.BLACK))
    white = staticmethod(factory(colorama.Fore.WHITE))


def augment(extra_parameters: Iterable[str]):
    """Applies augmentations to the function. \ 
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
        for key in extra_parameters:
            wrapper = decorators[key](wrapper)

        return unpacker(wrapper, len(extra_parameters))

    return decorator


def static(**vars):
    def decorate(func):
        for k, v in vars.items():
            setattr(func, k, v)
        return func

    return decorate


if __name__ == "__main__":
    pprint.e("ERROR", "some other", "message", [1, True, dict()])
    pprint.w("WARNING", "some other", "message", [1, True, dict()])
    pprint.s("SUCCESS", "some other", "message", [1, True, dict()])
    pprint.i1("INFO 1", "some other", "message", [1, True, dict()])
    pprint.i2("INFO 2", "some other", "message", [1, True, dict()])
    pprint.i3("INFO 3", "some other", "message", [1, True, dict()])

    print(color.e("ERROR"), "some other", "message", [1, True, dict()])
    print(color.w("WARNING"), "some other", "message", [1, True, dict()])
    print(color.s("SUCCESS"), "some other", "message", [1, True, dict()])
    print(color.i1("INFO 1"), "some other", "message", [1, True, dict()])
    print(color.i2("INFO 2"), "some other", "message", [1, True, dict()])
    print(color.i3("INFO 3"), "some other", "message", [1, True, dict()])
