import json

from .settman import settings
from .manager import import_


def translate(text: str | list, sep=" "):
    lang = settings.pull("user-prefs/language")
    lang = settings.pull("languages").get(lang) or ""
    trn = json.loads(import_("data/translator.json", 'io').read().decode()).get(lang)

    if not trn:
        return text

    full_text = []

    if type(text) is list:
        for tx in text:
            full_text.append(trn.get(tx.lower()) or tx)

        return sep.join(full_text)

    return trn.get(text.lower()) or (text if type(text) is str else sep.join(text))
