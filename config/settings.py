"""Global settings and constants for the Plot Generator application."""

from pathlib import Path

# Application settings
APP_NAME = "Publication Plot Generator"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Generate publication-quality plots for academic papers"

# Paths
BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
EXAMPLES_DIR = BASE_DIR / "examples"
TEMP_DIR = BASE_DIR / "temp"
EXPORTS_DIR = BASE_DIR / "exports"

# Create directories if they don't exist
TEMP_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

# Plot settings
DEFAULT_DPI = 300
DEFAULT_FIGURE_SIZE = (3.5, 2.625)  # Single column IEEE
DOUBLE_COLUMN_SIZE = (7.16, 5.37)   # Double column IEEE

# Export formats
EXPORT_FORMATS = {
    'PNG': {'extension': '.png', 'dpi': 300},
    'PDF': {'extension': '.pdf', 'dpi': 300},
    'SVG': {'extension': '.svg', 'dpi': None},
    'EPS': {'extension': '.eps', 'dpi': 300},
}

# File upload settings
MAX_FILE_SIZE = 100  # MB
ALLOWED_DATA_FORMATS = ['.csv', '.xlsx', '.xls', '.json', '.parquet']

# Style settings
DEFAULT_STYLE = 'ieee'
AVAILABLE_STYLES = ['ieee', 'nature', 'science', 'default', 'seaborn', 'ggplot']

# Font settings
DEFAULT_FONT_SIZE = 10
DEFAULT_FONT_FAMILY = 'serif'
DEFAULT_FONT = 'Times New Roman'

# Color settings
MAX_COLORS = 10
DEFAULT_COLOR_PALETTE = 'colorblind'

# LaTeX settings
USE_LATEX = False  # Set to True if LaTeX is installed
LATEX_PREAMBLE = r'\usepackage{amsmath}\usepackage{amssymb}'

# Performance settings
CACHE_ENABLED = True
CACHE_TTL = 3600  # seconds
MAX_DATA_POINTS = 1_000_000

# Streamlit settings
STREAMLIT_THEME = {
    'primaryColor': '#1f77b4',
    'backgroundColor': '#ffffff',
    'secondaryBackgroundColor': '#f0f2f6',
    'textColor': '#262730'
}