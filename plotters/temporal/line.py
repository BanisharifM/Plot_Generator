"""Line plot implementation."""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List
from core.base_plotter import BasePlotter, PlotConfig


class LinePlotter(BasePlotter):
    """Create line plots for temporal data."""
    
    name = "Line Plot"
    category = "temporal"
    description = "Display trends over time or continuous data"
    required_columns = 1
    supports_multiple_series = True
    
    def __init__(self, data: pd.DataFrame, config: Optional[PlotConfig] = None):
        """Initialize line plotter."""
        super().__init__(data, config)
        self.x_column = None
        self.y_columns = []
        self.colors = None
        self.line_styles = None
        self.markers = None
    
    def validate_data(self) -> bool:
        """Validate data for line plot."""
        if self.data is None or self.data.empty:
            return False
        
        # Need at least 2 columns (x and y)
        if len(self.data.columns) < 2:
            return False
        
        return True
    
    def set_columns(self, x_column: str, y_columns: List[str]):
        """Set the columns to plot."""
        self.x_column = x_column
        self.y_columns = y_columns if isinstance(y_columns, list) else [y_columns]
    
    def set_styles(self, colors: Optional[List[str]] = None, 
                  line_styles: Optional[List[str]] = None,
                  markers: Optional[List[str]] = None):
        """Set line styles."""
        self.colors = colors or plt.cm.tab10(np.linspace(0, 1, len(self.y_columns)))
        self.line_styles = line_styles or ['-'] * len(self.y_columns)
        self.markers = markers or [''] * len(self.y_columns)
    
    def create_plot(self) -> Tuple[plt.Figure, plt.Axes]:
        """Create the line plot."""
        # Create figure
        fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)
        
        # Set default columns if not set
        if not self.x_column or not self.y_columns:
            self.x_column = self.data.columns[0]
            self.y_columns = [col for col in self.data.columns[1:] 
                            if pd.api.types.is_numeric_dtype(self.data[col])]
        
        # Set default styles if not set
        if not self.colors:
            self.set_styles()
        
        # Plot each series
        for i, y_col in enumerate(self.y_columns):
            color = self.colors[i] if i < len(self.colors) else None
            linestyle = self.line_styles[i] if self.line_styles and i < len(self.line_styles) else '-'
            marker = self.markers[i] if self.markers and i < len(self.markers) else ''
            
            ax.plot(self.data[self.x_column], 
                   self.data[y_col],
                   label=y_col,
                   color=color,
                   linestyle=linestyle,
                   marker=marker,
                   linewidth=self.config.line_width,
                   markersize=self.config.marker_size,
                   alpha=self.config.alpha)
        
        # Rotate x labels if dates
        if pd.api.types.is_datetime64_any_dtype(self.data[self.x_column]):
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        self.figure = fig
        self.axes = ax
        
        return fig, ax
    
    @classmethod
    def get_required_params(cls):
        """Get required parameters."""
        return {
            'x_column': str,
            'y_columns': list,
        }
    
    @classmethod
    def get_optional_params(cls):
        """Get optional parameters."""
        return {
            'colors': list,
            'line_styles': list,
            'markers': list,
            'smooth': bool,
            'fill_between': bool,
        }