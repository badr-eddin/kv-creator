

class Mak:
    FUNCTIONS = ["on_save_settings"]

    colors = {
        "background_c": "#0d0d0d",
        "head_c": "#191C1F",
        "border_c": "#97B0B8",
        "shadow_c": "#000000",
        "primary_c": "#32926F"
    }

    palette = {
        "$MAIN": colors.get("primary_c"),
        "$WIDGET-1": colors.get("head_c"),
        "$BACKGROUND": colors.get("background_c"),
        "$BORDER": colors.get("border_c"),
        "$WIDGET-2": "#0D1117",
        "$WIDGET-2-H": "#13181E",
        "$FONT": "Ubuntu Mono",
        "$FONT-SIZE": "13px",
        "$FOREGROUND": "#FFFFFF",
        "$SELECTION-COLOR": "#000000"
    }

    name = "Mak"

    def load(self, main):
        theme = main.std.import_("plugins/mak/mak.qss", 'io').read().decode()

        for k in self.palette:
            v = self.palette[k]
            theme = theme.replace('"' + k + '"', v)

        theme = theme.replace("$ROOT", "./icons")

        return theme

    @staticmethod
    def on_save_settings(kw):
        if not kw.get("self"):
            return

        kw.get("self").main.load_theme()


CLASS = Mak
VERSION = 0.1
TYPE = "theme/qss"
NAME = "Mak"
