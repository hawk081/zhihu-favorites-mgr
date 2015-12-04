# -*- coding: utf-8 -*-
import re

class Enum(set):
    def __init__(self, items, **kwargs):
        current = 0
        previous = -1
        generator = lambda x: x + 1
        re_item_obj = re.compile(r"(?P<name>\w+)(?:=(?P<value>.+))?")
        for item in items:
            result = re_item_obj.search(item.strip().replace(' ', ''))
            if result:
                name = result.group('name')
                value = result.group('value')
                if value is not None:
                    current = eval(self._replace_attr_with_value(value) )
                else:
                    current = generator(previous)

                if not hasattr(self, name):
                    setattr(self, name, current)
                else:
                    raise AttributeError("Duplicated enum names: %s" % name)
                previous = current
            else:
                raise AttributeError("enum name error!")

    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError

    def _getValue(self, data):
        def _check_number(s):
            if s[0] in ('-', '+'):
                return s[1:].isdigit()
            return s.isdigit()

        value = data
        if not _check_number(data):
            if hasattr(self, data):
                value = getattr(self, data)
            else:
                raise AttributeError("No Attribute named %s" % data)
        return value

    def _replace_attr_with_value(self, exp):
        variables_obj = re.compile(r"(\w+)")
        variables = variables_obj.findall(exp)
        for variable in variables:
            exp = exp.replace(variable, str(self._getValue(variable)))
        return exp

if __name__ == '__main__':
    # basic
    wID = Enum([
        "DOG=11", "CAT = DOG + 2 * (3 % 2)", "HORSE", "DESK", "FISH",
    ])
    print wID.DOG,wID.CAT,wID.HORSE,wID.DESK,wID.FISH

    # Duplicated names
    wDuplicateID = Enum([
        "DOG", "CAT", "DOG"
    ]) # Duplicated enum names
