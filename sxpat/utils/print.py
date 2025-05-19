# typing
from typing import Callable, Any

import colorama


class color:
    def factory(color: str) -> Callable[[str], str]:
        return lambda s: color + s + colorama.Fore.RESET

    with_color = staticmethod(factory)

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

    with_color = staticmethod(factory)

    s = success = green = staticmethod(factory(colorama.Fore.GREEN))
    w = warning = yellow = staticmethod(factory(colorama.Fore.YELLOW))
    e = error = red = staticmethod(factory(colorama.Fore.RED))
    i1 = info1 = cyan = staticmethod(factory(colorama.Fore.CYAN))
    i2 = info2 = blue = staticmethod(factory(colorama.Fore.BLUE))
    i3 = info3 = magenta = staticmethod(factory(colorama.Fore.MAGENTA))
    black = staticmethod(factory(colorama.Fore.BLACK))
    white = staticmethod(factory(colorama.Fore.WHITE))


if __name__ == '__main__':
    pprint.e('ERROR', 'some other', 'message', [1, True, dict()])
    pprint.w('WARNING', 'some other', 'message', [1, True, dict()])
    pprint.s('SUCCESS', 'some other', 'message', [1, True, dict()])
    pprint.i1('INFO 1', 'some other', 'message', [1, True, dict()])
    pprint.i2('INFO 2', 'some other', 'message', [1, True, dict()])
    pprint.i3('INFO 3', 'some other', 'message', [1, True, dict()])

    print(color.e('ERROR'), 'some other', 'message', [1, True, dict()])
    print(color.w('WARNING'), 'some other', 'message', [1, True, dict()])
    print(color.s('SUCCESS'), 'some other', 'message', [1, True, dict()])
    print(color.i1('INFO 1'), 'some other', 'message', [1, True, dict()])
    print(color.i2('INFO 2'), 'some other', 'message', [1, True, dict()])
    print(color.i3('INFO 3'), 'some other', 'message', [1, True, dict()])
