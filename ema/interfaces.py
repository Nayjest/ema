from enum import Enum


class Interface(str, Enum):
    SLACK = "slack"
    UNKNOWN = "unknown"
    CLI = "cli"

    def __str__(self):
        return self.value
