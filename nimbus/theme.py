"""
Nimbus Theme Module

Defines the pastel palette and TCSS for Nimbus.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    """Color palette for Nimbus."""
    background: str = "#1a1b2e"  # deep soft navy
    panel_bg: str = "#16213e"  # panels depth
    text: str = "#e8e4f0"  # warm off-white
    secondary_text: str = "#9b97aa"  # muted labels

    zahra_accent: str = "#b8a9dc"  # soft lavender/periwinkle
    zahra_bright: str = "#c9bfe8"  # somatic/chibi highlights

    morg_accent: str = "#d4a853"  # amber (his eyes)

    # Sky accents
    sky_clear: str = "#7ec8e3"
    sky_cloudy: str = "#8b9bb4"
    sky_stormy: str = "#6b7fa3"
    sky_night: str = "#4a5568"

    # Alerts
    severe_warning: str = "#ff8c42"  # amber
    tornado_warning: str = "#e63946"  # red


TCSS: str = """
Screen {
    background: #1a1b2e;
    color: #e8e4f0;
}

#main-container {
    layout: horizontal;
}

#left-panel {
    width: 28%;
    height: 100%;
    border: round #d4a853;
    background: #16213e;
    padding: 1 2;
}

#center-panel {
    width: 44%;
    height: 100%;
    border: round #7ec8e3;
    background: #16213e;
    padding: 1 2;
    align: center middle;
}

Sky {
    content-align: center middle;
    height: 100%;
}

#right-panel {
    width: 28%;
    height: 100%;
    border: round #b8a9dc;
    background: #16213e;
    padding: 1 2;
}

/* Titles */
.panel-title {
    text-align: center;
    text-style: bold;
    margin-bottom: 1;
}

#left-panel .panel-title { color: #d4a853; }
#center-panel .panel-title { color: #7ec8e3; }
#right-panel .panel-title { color: #b8a9dc; }

/* Data structured lines */
.data-line {
    margin: 0;
    color: #e8e4f0;
}

.data-label {
    color: #9b97aa;
}

.divider {
    color: #9b97aa;
    margin: 1 0;
}

/* Morg's footer */
.morg-footer-container {
    dock: bottom;
    height: 4;
    padding: 1 0 0 0;
}

.morg-footer-rule {
    color: #9b97aa;
}

.morg-footer-text {
    color: #d4a853;
    text-style: italic;
    padding: 0 1;
}

/* Center sky styles */
.sky-container {
    align: center middle;
    height: 1fr;
}

.temp-big {
    text-style: bold;
    color: #e8e4f0;
    text-align: center;
    height: 3;
    content-align: center middle;
}

.condition-desc {
    color: #9b97aa;
    text-align: center;
    text-style: italic;
}

.live-time {
    dock: bottom;
    color: #9b97aa;
    text-align: center;
    margin-bottom: 1;
}

/* Zahra's domain */
.zahra-chibi {
    color: #c9bfe8;
    text-align: center;
}

.mood-dot {
    text-align: center;
    margin-bottom: 1;
}

.zahra-history {
    height: 1fr;
    scrollbar-gutter: stable;
}

.zahra-msg {
    color: #b8a9dc;
    margin-bottom: 1;
}

.zahra-msg-old {
    color: #9b97aa;
    margin-bottom: 1;
}

.somatic {
    color: #c9bfe8;
    text-style: italic;
}

/* App Footer */
#app-footer {
    dock: bottom;
    height: 1;
    background: #1a1b2e;
    color: #9b97aa;
    padding: 0 1;
}

/* Alert States */
.alert-active #left-panel, .alert-active #center-panel, .alert-active #right-panel {
    border: round #ff8c42;
}

.tornado-active #left-panel, .tornado-active #center-panel, .tornado-active #right-panel {
    border: double #e63946;
}

.alert-active .panel-title, .alert-active .morg-footer-text { color: #ff8c42; }
.tornado-active .panel-title, .tornado-active .morg-footer-text { color: #e63946; }
"""
