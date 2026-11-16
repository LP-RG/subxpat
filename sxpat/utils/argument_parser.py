# Based on `argparse_dataclass` by Michael V. DePalantis and contributors
# repository: https://github.com/mivade/argparse_dataclass
#
# Updated for python 3.14, fixed, and customised for SubXPAT by Marco Biasion.
#
# Original license:
# ==============================================================================
# MIT License
#
# Copyright (c) 2019-2023 argparse_dataclass contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================


import argparse
import enum
import re
from types import NoneType
from typing import (
    Any,
    ClassVar,
    Iterable,
    NoReturn,
    Optional,
    Sequence,
    get_origin,
    get_type_hints,
    Literal,
    get_args,
    Union,
)
from dataclasses import (
    Field,
    is_dataclass,
    _FIELDS,  # this may be an issue as it may be an implementation detail # pyright: ignore[reportAttributeAccessIssue]
    MISSING,
    InitVar,
)


ArgsType = Optional[Iterable[str]]


def add_dataclass_options[OT](
    options_class: type[OT], parser: argparse.ArgumentParser
) -> None:
    if not is_dataclass(options_class):
        raise TypeError("cls must be a dataclass")

    dc_types = get_type_hints(options_class)

    for field in getattr(options_class, _FIELDS).values():
        arg_metadata: Optional[dict] = field.metadata.get('argument')
        if arg_metadata is None: continue

        # get field type (also from InitVar)
        field_type: Optional[type] = dc_types.get(field.name)
        if isinstance(field_type, InitVar): field_type = field_type.type

        # prepare kwargs for argument constructor
        action = arg_metadata.get("action", None)
        if hasattr(action, "format_value"): _format_default = action.format_value  # pyright: ignore
        else: _format_default = lambda d: d
        kwargs = {
            "type": arg_metadata.get("type", field_type),
            "help": arg_metadata.get("help", '').format(default=_format_default(field.default)),
        }

        # generate names
        positional = arg_metadata.get('positional', False)
        args: list[str] = arg_metadata.get('args', [])
        if not args:
            if positional:
                args.append(field.name)
                kwargs['metavar'] = _get_arg_name(field)
            else:
                _arg_name = f'--{_get_arg_name(field)}'
                args.append(_arg_name)
        args.extend(arg_metadata.get('aliases', []))

        # We want to ensure that we store the argument based on the
        # name of the field and not whatever flag name was provided
        if arg_metadata.get("args") and not positional:
            kwargs["dest"] = field.name

        if (_choices := arg_metadata.get("choices")) is not None:
            kwargs["choices"] = _choices

        # Support Literal types as an alternative means of specifying choices.
        _field_origin = get_origin(field_type)
        if _field_origin is Literal:
            # Prohibit a potential collision with the choices field
            if arg_metadata.get("choices") is not None:
                raise ValueError(
                    f"Cannot infer type of items in field: {field.name}. "
                    "Literal type arguments should not be combined with choices in the metadata. "
                    "Remove the redundant choices field from the metadata."
                )

            # Get the types of the arguments of the Literal
            types = [type(arg) for arg in get_args(field_type)]

            # Make sure just a single type has been used
            if len(set(types)) > 1:
                raise ValueError(
                    f"Cannot infer type of items in field: {field.name}. "
                    "Literal type arguments should contain choices of a single type. "
                    f"Instead, {len(set(types))} types where found: "
                    + ", ".join([type_.__name__ for type_ in set(types)])
                    + "."
                )

            # Overwrite the type kwarg
            kwargs["type"] = types[0]
            # Use the literal arguments as choices
            kwargs["choices"] = get_args(field_type)

        if (_metavar := arg_metadata.get("metavar")) is not None:
            kwargs["metavar"] = _metavar

        if (_nargs := arg_metadata.get("nargs")) is not None:
            kwargs["nargs"] = _nargs
            if arg_metadata.get("type") is None:
                # When nargs is specified, field.type should be a list,
                # or something equivalent, like typing.List.
                # Using it would most likely result in an error, so if the user
                # did not specify the type of the elements within the list, we
                # try to infer it:
                try:
                    kwargs["type"] = get_args(field_type)[0]  # get_args returns a tuple
                except IndexError:
                    # get_args returned an empty tuple, type cannot be inferred
                    raise ValueError(
                        f"Cannot infer type of items in field: {field.name}. "
                        "Try using a parameterized type hint, or "
                        "specifying the type explicitly using metadata['type']"
                    )

        if arg_metadata.get("required"):
            kwargs["required"] = True

        elif field.default != MISSING:
            kwargs["default"] = field.default

        if action is not None:
            kwargs['action'] = action

        elif field_type is bool:
            _handle_bool_type(field, args, kwargs)

        elif get_origin(field_type) is Union:
            if arg_metadata.get("type") is None:
                # Optional[X] is equivalent to Union[X, None].
                f_args = get_args(field_type)
                if len(f_args) == 2 and NoneType in f_args:
                    arg = next(a for a in f_args if a is not NoneType)
                    kwargs["type"] = arg
                else:
                    raise TypeError(
                        "For Union types other than 'Optional', a custom 'type' must be specified using "
                        "'metadata'."
                    )

        if "group" in arg_metadata:
            _action = _handle_argument_group(parser, field, args, kwargs)
        else:
            _action = parser.add_argument(*args, **kwargs)

        arg_metadata['_action'] = _action


def _handle_bool_type(field: Field, args: list, kwargs: dict):
    """
    Handles configuring the parser argument for boolean types.

    Different field configurations:
        If `required` is specified: action=`BooleanOptionalAction`
        No default value specified: action=`store_true`
        Default value set to `True` : action=`store_false`
            (and add a `no-` prefix to the name if no custom args specified)
        Default value set to `False`: action=`store_true`
    """

    kwargs["action"] = "store_true"
    for key in ("type", "required"): kwargs.pop(key, None)
    arg_metadata: dict = field.metadata.get('argument')  # always valid # pyright: ignore

    if arg_metadata.get("required") is True:
        kwargs["action"] = argparse.BooleanOptionalAction
        kwargs["required"] = True
    elif "default" in kwargs:
        if field.default is True:
            kwargs["action"] = "store_false"
            if "args" not in arg_metadata:
                args[0] = f"--no-{_get_arg_name(field)}"
                kwargs["dest"] = field.name


def _handle_argument_group(
    parser: argparse.ArgumentParser,
    field: Field,
    args: list,
    kwargs: dict
) -> argparse.Action:
    """Handles adding the argument to an argument group."""

    arg_metadata: dict = field.metadata.get('argument')  # always valid # type: ignore

    # get target group specifications
    group = arg_metadata.get("group")
    if isinstance(group, str):
        title = group
        description = None
    elif isinstance(group, dict):
        title = group.get("title")
        description = group.get("description")
    else:
        raise TypeError("'group' must be a group title or a dictionary")

    # get target group if already exists or create if missing
    group = next((x for x in parser._action_groups if x.title == title), None)
    if group is None:
        group = parser.add_argument_group(title, description)

    return group.add_argument(*args, **kwargs)


def _get_arg_name(field: Field):
    return field.name.replace("_", "-")


class CustomActionBase(argparse.Action):
    """
    :authors: Marco Biasion
    """

    def _single_check(self,
                      parser: argparse.ArgumentParser,
                      values: str | Sequence[Any] | None,
                      option_string: str | None
                      ) -> str:
        if values is None: self._error(parser, option_string)
        if not isinstance(values, str): self._error(parser, option_string)
        return values

    def _error(self, parser: argparse.ArgumentParser, option_string: str | None) -> NoReturn:
        if option_string is None: parser.error(f'unable to parse `{self.metavar}`.')
        else: parser.error(f'unable to parse `{self.option_strings}`.')


class EnumChoicesAction(CustomActionBase):
    """
    Custom argparse.Action to use enumerator as choices.

    Include formatting from enum to string, and parsing from string to enum.

    Note that the formatted value of an enum will always be a string,
    but the parsed value should be a concrete value assigned to an entry of an enum class.
    For this reason, this mostly works with string enums.

    :authors: Marco Biasion
    """

    def __init__(self, *args, type: type[enum.Enum], **kwargs) -> None:
        super().__init__(*args, **kwargs, choices=[self.format_value(e) for e in type])
        self.enum = type

    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace,
                 values: str | Sequence[Any] | None, option_string: str | None = None) -> None:
        value = self._single_check(parser, values, option_string)

        try: setattr(namespace, self.dest, self.enum(value))
        except: self._error(parser, option_string)

    @classmethod
    def format_value(cls, value: enum.Enum | None) -> str:
        if isinstance(value, enum.Enum): return str(value.value)
        return '???'


class TimeDeltaAction(CustomActionBase):
    """
    Custom argparse.Action for use in parsing time deltas to seconds.

    A time delta is any sequence of digits, followed by:
    - `S` / `s` / nothing : seconds
    - `M` / `m` : minutes
    - `H` / `h` : hours
    - `D` / `d` : days

    :authors: Marco Biasion
    """

    _PATTERN: ClassVar = re.compile(r'(\d+)([smhd]?)')
    _MULTS: ClassVar = {'S': 1, '': 1, 'M': 60, 'H': 60 * 60, 'D': 60 * 60 * 24}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace,
                 values: str | Sequence[Any] | None, option_string: str | None = None) -> None:
        value = self._single_check(parser, values, option_string)

        # recompose seconds
        seconds = self.parse_value(value)
        if seconds is None: self._error(parser, option_string)
        setattr(namespace, self.dest, seconds)

    def parse_value(self, raw: str) -> int | None:
        m = self._PATTERN.match(raw)
        if m is None: return None
        return int(m[1]) * self._MULTS[m[2].upper()]

    @classmethod
    def format_value(cls, value: int | None) -> str:
        if isinstance(value, int):
            if value == 0: return 'none'
            if value % 60 != 0: return f'{value}s'
            if (v := value // 60) % 60 != 0: return f'{v}m'
            if (v := v // 60) % 24 != 0: return f'{v}h'
            else: return f'{v // 24}d'
        return '???'
