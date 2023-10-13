from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class FilenameValidator:
    messages = {
        'not_allowed_symbol': 'Symbol "%(not_allowed_symbol)s" is not allowed',
        'endswith': 'Symbol "." must not be a last symbol',
    }
    not_allowed_symbols = '/\\<>:|?*\000"%+!@~'

    def __call__(self, value):
        """
        https://learn.microsoft.com/ru-ru/windows/win32/fileio/naming-a-file
        https://ru.wikipedia.org/wiki/%D0%98%D0%BC%D1%8F_%D1%84%D0%B0%D0%B9%D0%BB%D0%B0
        """
        value_as_set = set(value)
        for symbol in self.not_allowed_symbols:
            if symbol in value_as_set:
                raise ValidationError(
                    self.messages['not_allowed_symbol'],
                    code='not_allowed_symbol',
                    params={'not_allowed_symbol': symbol, 'value': value},
                )

        if value.endswith('.'):
            raise ValidationError(
                self.messages['endswith'],
                code='endswith',
                params={'value': value},
            )

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        return self.messages == other.messages and self.not_allowed_symbols == other.not_allowed_symbols
