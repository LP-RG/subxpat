
import string as _string
from textwrap import dedent


class PartialFormatter(_string.Formatter):
    """
    :authors: Marco Biasion
    """

    def vformat(self, format_string, args, kwargs):
        result = []

        for (literal, field_name, format_spec, conversion) in self.parse(format_string):
            result.append(literal)
            if field_name is None: continue

            try:
                obj, _ = self.get_field(field_name, args, kwargs)
            except (KeyError, IndexError, AttributeError):
                placeholder = '{' + field_name
                if conversion:
                    placeholder += '!' + conversion
                if format_spec:
                    placeholder += ':' + format_spec
                placeholder += '}'
                result.append(placeholder)
                continue

            if conversion:
                obj = self.convert_field(obj, conversion)
            if format_spec:
                format_spec = self.vformat(format_spec, args, kwargs)

            result.append(self.format_field(obj, format_spec))

        return ''.join(result)


partial_format = PartialFormatter().format
