from typing import Optional

from utils.regexp import RegExp


class PhoneNumberUtils:

    @staticmethod
    def get_variants(value) -> list:
        if value and isinstance(value, str):
            return [i for i in [value, value[1:], f'7{value[1:]}', f'7{value}', f'8{value[1:]}']]
        return []

    @staticmethod
    def sanitize(value) -> Optional[str]:
        if value and isinstance(value, str):
            return ''.join(filter(str.isnumeric, value))
        return None

    @staticmethod
    def normalize(value, strict=True) -> Optional[str]:
        if value and isinstance(value, str):
            if value == 'anonymous':
                return None

            value = PhoneNumberUtils.sanitize(value)

            if len(value) == 10:
                value = f'7{value}'
            elif len(value) == 11 and value.startswith('8'):
                value = f'7{value[1:]}'

            if strict:
                if RegExp.is_valid_phone(value):
                    return value
            else:
                return value

        return None
