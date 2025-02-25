from enum import Enum

from dotenv import load_dotenv

load_dotenv()


class Provider(Enum):
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"


class DimensionType(Enum):
    HORIZONTAL = {
        Provider.VIDEO: (1920, 1080),
        Provider.IMAGE: (1792, 1024)
    }
    VERTICAL = {
        Provider.VIDEO: (1080, 1920),
        Provider.IMAGE: (1024, 1792)
    }

    def get(self, provider: Provider):
        return self.value.get(provider, (None, None))

    _default = HORIZONTAL

    @classmethod
    def get_default(cls):
        return cls._default
