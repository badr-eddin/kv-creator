import json
import re

from .settman import settings


class pan:
    @staticmethod
    def load(prop, value):
        props = settings.pull("kivy/properties")

        prop_type = str(props.get(prop)).lower()

        if re.match(".*string.*", prop_type):
            _value = ('"' if not str(value).startswith('"') else '') +\
                     str(value) + \
                     ('"' if not str(value).endswith('"') else '')
            return json.loads(_value)

        if re.match(".*numeric.*", prop_type):
            _digits = re.findall(r"\d", value)
            return "".join(_digits)

        return value

    @staticmethod
    def dump(prop, value):
        props = settings.pull("kivy/properties")

        prop_type = str(props.get(prop)).lower()

        if re.match(".*string.*", prop_type):
            if not (str(value).startswith('"') and str(value).endswith('"')):
                return json.dumps(value)

        if re.match(".*numeric.*", prop_type):
            _digits = re.findall(r"\d", value)
            return "".join(_digits)

        return value
