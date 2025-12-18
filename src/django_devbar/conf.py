from django.conf import settings

POSITIONS = {
    "bottom-right": "bottom:0;right:0",
    "bottom-left": "bottom:0;left:0",
    "top-right": "top:0;right:0",
    "top-left": "top:0;left:0",
}


def get_config():
    return {
        "POSITION": "bottom-right",
        "SHOW_BAR": None,  # None = use settings.DEBUG
        "SHOW_HEADERS": False,
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
