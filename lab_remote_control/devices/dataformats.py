from typing import Optional


class NR2(float):

    def __new__(cls, param, *args, **kwargs):
        if isinstance(param, str):
            value, _ = cls.cast_unit(param)
        else:
            value = param
        return super().__new__(cls, value, *args, **kwargs)

    def __init__(self, param, *args, **kwargs):
        self.value, self.unit = self.cast_unit(param)
        super().__init__(*args, **kwargs)

    @staticmethod
    def cast_unit(value):
        """
        Parses a value and its unit (if any) from a string
        of the form '<number><unit>'.
        For example: 10s returns 10.0, 's'

        :param value: str of the form '<number><unit>'
        :return: tuple of the form: (<number>, '<unit>')
        """
        unit: Optional[str] = None
        value_: float
        while value:
            try:
                value_ = float(value)
                if unit:
                    unit = unit.strip('\n').strip(' ')
                return value_, unit
            except ValueError:
                if value[-1] != ' ':
                    unit = value[-1] + (unit or '')
                value = value[:-1]
        else:
            raise ValueError(f'parsing value {value} failed')

    def __str__(self, unit=True):
        if unit:
            if self.unit:
                return ' '.join([str(self.value), self.unit])
            else:
                return str(self.value)
        else:
            return str(self.value)

    def __repr__(self):
        return self.__str__()


class NR3(NR2):

    def __new__(cls, param, *args, **kwargs):
        value, unit = cls.cast_unit(param)
        if unit:
            if unit[0] == 'k' or unit[0] == 'K':
                value = value * 10**3
        return super().__new__(cls, value, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.unit:
            if self.unit[0] == 'k' or self.unit[0] == 'K':
                self.value = self.value * 10**3
                self.reverse_multiplier = 10**-3
                self.unit = self.unit[1:]
            else:
                self.reverse_multiplier = 1

    def apply_multiplier(self):
        return self * self.reverse_multiplier

    def __str__(self, reverse_multiplier=False):
        if reverse_multiplier:
            return ' '.join([str(self.apply_multiplier()), 'k' + self.unit])
        else:
            return ' '.join([str(self.value), self.unit])
