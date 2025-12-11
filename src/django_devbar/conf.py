from django.conf import settings

POSITIONS = {
    "bottom-right": "bottom:0;right:0",
    "bottom-left": "bottom:0;left:0",
    "top-right": "top:0;right:0",
    "top-left": "top:0;left:0",
}

DEFAULT_THRESHOLDS = {
    "time_warning": 500,
    "time_critical": 1500,
    "count_warning": 20,
    "count_critical": 50,
}


def get_position():
    key = getattr(settings, "DEVBAR_POSITION", "bottom-right")
    return POSITIONS.get(key, POSITIONS["bottom-right"])


def get_show_bar():
    return getattr(settings, "DEVBAR_SHOW_BAR", settings.DEBUG)


def get_show_headers():
    return getattr(settings, "DEVBAR_SHOW_HEADERS", False)


def get_enable_console():
    return getattr(settings, "DEVBAR_ENABLE_CONSOLE", True)


def get_thresholds():
    user_thresholds = getattr(settings, "DEVBAR_THRESHOLDS", {})
    final = DEFAULT_THRESHOLDS.copy()
    final.update(user_thresholds)
    return final
