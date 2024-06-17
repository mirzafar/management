import re


class RegExp:
    IIN = re.compile(r'^\d{12}$')
    PHONE = re.compile(r'^7[79]\d{9}$')
    SENDER = re.compile(r'\w+:\w+:.+')
    TRACK_ID = re.compile(r'(\w{2}\d{8})|(^[a-zA-Z]\d{8}[a-zA-Z]$)')
    EMAIL = re.compile(r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,4})+$')

    @staticmethod
    def is_valid_iin(iin) -> bool:
        def get_mod_11(l):
            return sum([x * y for x, y in l]) % 11

        if iin and isinstance(iin, str):
            if RegExp.IIN.fullmatch(iin):
                numbered_iin = [int(number) for number in iin]

                last = numbered_iin[-1]

                csum = get_mod_11(zip(numbered_iin, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]))
                if csum == 10:
                    csum = get_mod_11(zip(numbered_iin, [3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2]))

                return last == csum
        return False

    @staticmethod
    def is_valid_phone(phone) -> bool:
        if phone and isinstance(phone, str) and RegExp.PHONE.fullmatch(phone):
            return True
        return False

    @staticmethod
    def is_valid_sender(sender) -> bool:
        if sender and isinstance(sender, str) and RegExp.SENDER.fullmatch(sender):
            return True
        return False

    @staticmethod
    def is_valid_email(email) -> bool:
        if email and isinstance(email, str) and RegExp.EMAIL.fullmatch(email):
            return True
        return False

    @staticmethod
    def is_valid_track_id(track) -> bool:
        if track and isinstance(track, str) and RegExp.TRACK_ID.fullmatch(track):
            return True
        return False
