# themes.py

THEMES = {
    "dark": {
        "name": "Dark",
        "bg": "#121212",
        "surface": "#1E1E1E",
        "surface2": "#252525",
        "text": "#E0E0E0",
        "text_secondary": "#B0B0B0",
        "accent": "#007BFF",          # Blue accent
        "accent_hover": "#0056B3",
        "border": "#2A2A2A",
        "status": "#007BFF",
        "selected": "#007BFF",
    },
    "light": {
        "name": "Light",
        "bg": "#F5F5F5",
        "surface": "#FFFFFF",
        "surface2": "#F0F0F0",
        "text": "#212121",
        "text_secondary": "#666666",
        "accent": "#007BFF",
        "accent_hover": "#0056B3",
        "border": "#DDDDDD",
        "status": "#007BFF",
        "selected": "#007BFF",
    },
    "pink": {
        "name": "Pink",
        "bg": "#121212",
        "surface": "#1E1A1E",
        "surface2": "#2D1B2D",
        "text": "#FFE0FF",
        "text_secondary": "#FFB0FF",
        "accent": "#FF69B4",          # Hot pink
        "accent_hover": "#FF1493",
        "border": "#3A2A3A",
        "status": "#FF69B4",
        "selected": "#FF69B4",
    },
    "blue": {
        "name": "Blue",
        "bg": "#0A192F",
        "surface": "#132F4C",
        "surface2": "#1E3A5F",
        "text": "#E0F7FA",
        "text_secondary": "#80DEEA",
        "accent": "#00B0FF",
        "accent_hover": "#0091EA",
        "border": "#294D6F",
        "status": "#00B0FF",
        "selected": "#00B0FF",
    },
}

def get_stylesheet(theme_name: str) -> str:
    t = THEMES[theme_name]
    return f"""
    QWidget {{
        background-color: {t['bg']};
        color: {t['text']};
        font-family: 'Segoe UI', Arial, sans-serif;
    }}
    QLabel {{
        color: {t['text_secondary']};
        font-size: 14px;
    }}
    QPushButton {{
        background-color: {t['accent']};
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        min-width: 120px;
        font-size: 14px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {t['accent_hover']};
    }}
    QPushButton:disabled {{
        background-color: #555555;
        color: #888888;
    }}
    QComboBox {{
        background-color: {t['surface']};
        color: {t['text']};
        border: 1px solid {t['border']};
        padding: 10px;
        border-radius: 6px;
        min-width: 140px;
    }}
    QComboBox::drop-down {{
        border: none;
    }}
    QComboBox QAbstractItemView {{
        background-color: {t['surface']};
        color: {t['text']};
        selection-background-color: {t['accent']};
        selection-color: white;
        border: 1px solid {t['border']};
    }}
    QListWidget {{
        background-color: {t['surface']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 8px;
        border-radius: 4px;
    }}
    QListWidget::item:selected {{
        background-color: {t['selected']};
        color: white;
    }}
    QListWidget::item:hover {{
        background-color: {t['surface2']};
    }}
    QProgressBar {{
        background-color: {t['surface']};
        border: 1px solid {t['border']};
        border-radius: 4px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background-color: {t['accent']};
        border-radius: 4px;
    }}
    """