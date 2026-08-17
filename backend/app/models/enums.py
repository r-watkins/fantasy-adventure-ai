from enum import StrEnum


class MessageRole(StrEnum):
    PLAYER = "player"
    NARRATOR = "narrator"
    SYSTEM = "system"


class ThemePreference(StrEnum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"
