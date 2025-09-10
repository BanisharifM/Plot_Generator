"""Color palettes for plots."""

# Colorblind-safe palettes
COLORBLIND_SAFE = {
    'default': ['#0173B2', '#DE8F05', '#029E73', '#CC78BC', '#ECE133', '#56B4E9', '#F0E442'],
    'tol': ['#332288', '#117733', '#44AA99', '#88CCEE', '#DDCC77', '#CC6677', '#AA4499', '#882255'],
    'okabe_ito': ['#E69F00', '#56B4E9', '#009E73', '#F0E442', '#0072B2', '#D55E00', '#CC79A7'],
}

# Scientific journal palettes
JOURNAL_PALETTES = {
    'nature': ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4', '#91D1C2', '#DC0000'],
    'science': ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD', '#8C564B', '#E377C2', '#7F7F7F'],
    'ieee': ['#000000', '#0000FF', '#FF0000', '#00FF00', '#FF00FF', '#00FFFF', '#FFFF00', '#808080'],
}

# Categorical palettes
CATEGORICAL = {
    'set1': ['#E41A1C', '#377EB8', '#4DAF4A', '#984EA3', '#FF7F00', '#FFFF33', '#A65628', '#F781BF'],
    'set2': ['#66C2A5', '#FC8D62', '#8DA0CB', '#E78AC3', '#A6D854', '#FFD92F', '#E5C494', '#B3B3B3'],
    'set3': ['#8DD3C7', '#FFFFB3', '#BEBADA', '#FB8072', '#80B1D3', '#FDB462', '#B3DE69', '#FCCDE5'],
}

# Sequential palettes
SEQUENTIAL = {
    'blues': ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#08519c'],
    'greens': ['#f7fcf5', '#e5f5e0', '#c7e9c0', '#a1d99b', '#74c476', '#41ab5d', '#238b45', '#006d2c'],
    'reds': ['#fff5f0', '#fee0d2', '#fcbba1', '#fc9272', '#fb6a4a', '#ef3b2c', '#cb181d', '#a50f15'],
}

# Diverging palettes
DIVERGING = {
    'rdbu': ['#67001f', '#b2182b', '#d6604d', '#f4a582', '#fddbc7', '#d1e5f0', '#92c5de', '#4393c3', '#2166ac', '#053061'],
    'rdylgn': ['#a50026', '#d73027', '#f46d43', '#fdae61', '#fee08b', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850', '#006837'],
}

# Heatmap-specific colormaps
HEATMAP_PALETTES = {
    'diverging_rb': ['#053061', '#2166ac', '#4393c3', '#92c5de', '#d1e5f0', '#f7f7f7', '#fddbc7', '#f4a582', '#d6604d', '#b2182b', '#67001f'],
    'diverging_bg': ['#762a83', '#9970ab', '#c2a5cf', '#e7d4e8', '#f7f7f7', '#d9f0d3', '#a6dba0', '#5aae61', '#1b7837'],
    'sequential_heat': ['#ffffcc', '#ffeda0', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#bd0026', '#800026'],
    'sequential_cool': ['#f7fcf0', '#e0f3db', '#ccebc5', '#a8ddb5', '#7bccc4', '#4eb3d3', '#2b8cbe', '#0868ac', '#084081'],
    'viridis': ['#440154', '#482878', '#3e4989', '#31688e', '#26828e', '#1f9e89', '#35b779', '#6ece58', '#b5de2b', '#fde725'],
    'plasma': ['#0d0887', '#46039f', '#7201a8', '#9c179e', '#bd3786', '#d8576b', '#ed7953', '#fb9f3a', '#fdca26', '#f0f921'],
    'temperature': ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026'],
    'earth': ['#1a3620', '#2d5016', '#4a7c1e', '#73af48', '#a2d489', '#c8e4b5', '#e7f5de', '#faf0d4', '#e8c58b', '#d19c4c', '#a57328'],
}

def get_palette(name: str, n_colors: int = None):
    """Get a color palette by name.
    
    Args:
        name: Name of the palette
        n_colors: Number of colors to return
        
    Returns:
        List of hex color codes
    """
    # Handle custom palette from session state
    if name == 'custom':
        import streamlit as st
        if 'custom_colors' in st.session_state:
            return st.session_state.custom_colors
        return COLORBLIND_SAFE['default']
    
    # Check all palette dictionaries
    all_palettes = {
        **COLORBLIND_SAFE,
        **JOURNAL_PALETTES,
        **CATEGORICAL,
        **SEQUENTIAL,
        **DIVERGING,
        **HEATMAP_PALETTES,
    }
    
    if name in all_palettes:
        palette = all_palettes[name]
        if n_colors and n_colors != len(palette):
            # Interpolate colors if needed
            import matplotlib.colors as mcolors
            import numpy as np
            
            # Create a colormap from the palette
            cmap = mcolors.LinearSegmentedColormap.from_list('custom', palette)
            # Sample n_colors from the colormap
            colors = [mcolors.to_hex(cmap(i)) for i in np.linspace(0, 1, n_colors)]
            return colors
        return palette
    
    return COLORBLIND_SAFE['default']

def get_all_palette_names():
    """Get all available palette names."""
    return {
        'Colorblind Safe': list(COLORBLIND_SAFE.keys()),
        'Scientific Journals': list(JOURNAL_PALETTES.keys()),
        'Categorical': list(CATEGORICAL.keys()),
        'Sequential': list(SEQUENTIAL.keys()),
        'Diverging': list(DIVERGING.keys()),
        'Heatmap Colors': list(HEATMAP_PALETTES.keys()),
    }