"""Scatter plot implementation."""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Tuple, Optional
from core.base_plotter import BasePlotter, PlotConfig


class ScatterPlotter(BasePlotter):
    """Create scatter plots for statistical analysis."""
    
    name = "Scatter Plot"
    category = "statistical"
    description = "Visualize relationships between two continuous variables"
    required_columns = 2
    supports_multiple_series = True
    
    def __init__(self, data: pd.DataFrame, config: Optional[PlotConfig] = None):
        """Initialize scatter plotter."""
        super().__init__(data, config)
        self.x_column = None
        self.y_column = None
        self.size_column = None
        self.color_column = None
        self.fit_line = False
        self.confidence_band = False
    
    def validate_data(self) -> bool:
        """Validate data for scatter plot."""
        if self.data is None or self.data.empty:
            return False
        
        # Need at least 2 numeric columns
        numeric_cols = [col for col in self.data.columns 
                       if pd.api.types.is_numeric_dtype(self.data[col])]
        
        return len(numeric_cols) >= 2
    
    def set_columns(self, x_column: str, y_column: str,
                   size_column: Optional[str] = None,
                   color_column: Optional[str] = None):
        """Set the columns to plot."""
        self.x_column = x_column
        self.y_column = y_column
        self.size_column = size_column
        self.color_column = color_column
    
    def set_regression(self, fit_line: bool = False, 
                      confidence_band: bool = False):
        """Set regression line options."""
        self.fit_line = fit_line
        self.confidence_band = confidence_band
    
    def create_plot(self) -> Tuple[plt.Figure, plt.Axes]:
        """Create the scatter plot."""
        # Create figure
        fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)
        
        # Set default columns if not set
        if not self.x_column or not self.y_column:
            numeric_cols = [col for col in self.data.columns 
                          if pd.api.types.is_numeric_dtype(self.data[col])]
            if len(numeric_cols) >= 2:
                self.x_column = numeric_cols[0]
                self.y_column = numeric_cols[1]
        
        # Prepare data
        x = self.data[self.x_column]
        y = self.data[self.y_column]
        
        # Handle size
        if self.size_column and self.size_column in self.data.columns:
            sizes = self.data[self.size_column]
            # Normalize sizes
            sizes = 20 + 200 * (sizes - sizes.min()) / (sizes.max() - sizes.min())
        else:
            sizes = self.config.marker_size ** 2
        
        # Handle color
        if self.color_column and self.color_column in self.data.columns:
            if pd.api.types.is_numeric_dtype(self.data[self.color_column]):
                colors = self.data[self.color_column]
                scatter = ax.scatter(x, y, s=sizes, c=colors, 
                                   alpha=self.config.alpha, cmap='viridis')
                plt.colorbar(scatter, ax=ax, label=self.color_column)
            else:
                # Categorical color - use config colors if available
                categories = self.data[self.color_column].unique()
                if self.config.color_palette and len(self.config.color_palette) > 0:
                    colors = self.config.color_palette
                else:
                    from matplotlib import colors as mcolors
                    colors_array = plt.cm.tab10(np.linspace(0, 1, len(categories)))
                    colors = [mcolors.to_hex(c) for c in colors_array]
                
                for i, cat in enumerate(categories):
                    mask = self.data[self.color_column] == cat
                    ax.scatter(x[mask], y[mask], s=sizes if isinstance(sizes, (int, float)) else sizes[mask],
                             color=colors[i % len(colors)], alpha=self.config.alpha, label=cat)
        else:
            # Use first color from palette if available
            scatter_color = self.config.color_palette[0] if self.config.color_palette and len(self.config.color_palette) > 0 else None
            ax.scatter(x, y, s=sizes, alpha=self.config.alpha, color=scatter_color)
        
        # Add regression line if requested
        if self.fit_line:
            from scipy import stats
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            line_x = np.array([x.min(), x.max()])
            line_y = slope * line_x + intercept
            ax.plot(line_x, line_y, 'r-', linewidth=2, 
                   label=f'R² = {r_value**2:.3f}')
            
            # Add confidence band if requested
            if self.confidence_band:
                from scipy.stats import t
                predict_mean_se = std_err * np.sqrt(1/len(x) + 
                                                   (line_x - x.mean())**2 / 
                                                   np.sum((x - x.mean())**2))
                margin = t.ppf(0.975, len(x) - 2) * predict_mean_se
                ax.fill_between(line_x, line_y - margin, line_y + margin, 
                              color='red', alpha=0.2)
        
        self.figure = fig
        self.axes = ax
        
        return fig, ax
    
    @classmethod
    def get_required_params(cls):
        """Get required parameters."""
        return {
            'x_column': str,
            'y_column': str,
        }
    
    @classmethod
    def get_optional_params(cls):
        """Get optional parameters."""
        return {
            'size_column': str,
            'color_column': str,
            'fit_line': bool,
            'confidence_band': bool,
            'alpha': float,
            'marker_style': str,
        }