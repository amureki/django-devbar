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


def get_config():
    return {
        "POSITION": "bottom-right",
        "SHOW_BAR": None,  # None = use settings.DEBUG
        "SHOW_HEADERS": False,
        "ENABLE_CONSOLE": True,
        "EXTENSION_MODE": True,
        "THRESHOLDS": {},
        **getattr(settings, "DEVBAR", {}),
    }


def get_position():
    config = get_config()
    key = config["POSITION"]
    return POSITIONS.get(key, POSITIONS["bottom-right"])


def get_show_bar():
    config = get_config()
    show_bar = config["SHOW_BAR"]
    return settings.DEBUG if show_bar is None else show_bar


def get_show_headers():
    return get_config()["SHOW_HEADERS"]


def get_enable_console():
    return get_config()["ENABLE_CONSOLE"]


def get_extension_mode():
    return get_config()["EXTENSION_MODE"]


def get_thresholds():
    config = get_config()
    user_thresholds = config["THRESHOLDS"]
    final = DEFAULT_THRESHOLDS.copy()
    final.update(user_thresholds)
    return final
