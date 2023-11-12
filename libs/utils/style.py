import os


def load_style(style) -> str:
    if os.getenv("dev-env"):
        return style.replace("$", "src/")
    return style.replace("$", ":/")
