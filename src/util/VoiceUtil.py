from enum import Enum

from dotenv import load_dotenv

load_dotenv()


class VoiceType(Enum):
    JANE = "XrExE9yKIg1WjnnlVkGX"
    CALLUM = "N2lVS1w4EtoT3dr4eOWO"
    BILL = "pqHfZKP75CvOlQylNhV4"

    def get(self):
        return self.value

    def __str__(self):
        return self.value

    _default = BILL

    @classmethod
    def get_default(cls):
        return cls._default

    @classmethod
    def get_default_value(cls):
        return cls._default.get()