from frontend.resources import asset_path

# Color palette
BKG = "#F9FAFB"
SIDEBAR_BKG = "#E5E7EB"
PANEL_BKG = "#F9FAFB"
HEADER_BKG = "#111827"
ACCENT = "#2563EB"
ACCENT_HOVER = "#000080"
TEXT_PRIMARY = "#4B5563"
TEXT_SECONDARY = "#9CA3AF"
TEXT_ON_DARK = "#F9FAFB"
BORDERS = "#E5E7EB"
ROW_ALTERNATE = "#F3F4F6"
ROW_HOVER = "#E5E7EB"
ROW_SELECTED = "#7E9DDE"

# Screen sizes
SIDEBAR_MIN_WIDTH = 200
SIDEBAR_MAX_WIDTH = 400
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 600

_QSS_PATH = asset_path("frontend", "styles.qss")

_TOKENS = {
    "BKG":            BKG,
    "SIDEBAR_BKG":    SIDEBAR_BKG,
    "PANEL_BKG":      PANEL_BKG,
    "HEADER_BKG":     HEADER_BKG,
    "ACCENT":         ACCENT,
    "ACCENT_HOVER":   ACCENT_HOVER,
    "TEXT_PRIMARY":   TEXT_PRIMARY,
    "TEXT_SECONDARY": TEXT_SECONDARY,
    "TEXT_ON_DARK":   TEXT_ON_DARK,
    "BORDERS":        BORDERS,
    "ROW_ALTERNATE":  ROW_ALTERNATE,
    "ROW_HOVER":      ROW_HOVER,
    "ROW_SELECTED":   ROW_SELECTED,
}


def load_stylesheet() -> str:
    with open(_QSS_PATH, "r") as f:
        qss = f.read()
    for token, value in _TOKENS.items():
        qss = qss.replace(f"%{token}%", value)
    return qss
