from django.conf import settings

POSITIONS = {
    "bottom-right": "bottom:0;right:0",
    "bottom-left": "bottom:0;left:0",
    "top-right": "top:0;right:0",
    "top-left": "top:0;left:0",
}


def get_position():
    key = getattr(settings, "DEVBAR_POSITION", "bottom-right")
    return POSITIONS.get(key, POSITIONS["bottom-right"])


def get_show_bar():
    return getattr(settings, "DEVBAR_SHOW_BAR", settings.DEBUG)


def get_show_headers():
    return getattr(settings, "DEVBAR_SHOW_HEADERS", False)
