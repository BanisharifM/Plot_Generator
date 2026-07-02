"""Global settings and constants for the Plot Generator application."""

from pathlib import Path

APP_NAME = "Publication Plot Generator"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Generate publication-quality plots for academic papers"

BASE_DIR = Path(__file__).parent.parent
EXPORTS_DIR = BASE_DIR / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)

EXPORT_FORMATS = {
    'PNG': {'extension': '.png', 'dpi': 300},
    'PDF': {'extension': '.pdf', 'dpi': 300},
    'SVG': {'extension': '.svg', 'dpi': None},
    'EPS': {'extension': '.eps', 'dpi': 300},
}
