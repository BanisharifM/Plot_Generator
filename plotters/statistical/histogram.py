"""Histogram plot implementation."""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List
from core.base_plotter import BasePlotter, PlotConfig


class HistogramPlotter(BasePlotter):
    """Create histograms for distribution analysis."""
    
    name = "Histogram"
    category = "statistical"
    description = "Visualize the distribution of a continuous variable"
    required_columns = 1
    supports_multiple_series = True
    
    def __init__(self, data: pd.DataFrame, config: Optional[PlotConfig] = None):
        """Initialize histogram plotter."""
        super().__init__(data, config)
        self.value_column = None
        self.group_column = None
        self.bins = 30
        self.density = False
        self.cumulative = False
        self.kde = False
        self.stat = 'count'  # count, frequency, probability, density
    
    def validate_data(self) -> bool:
        """Validate data for histogram."""
        if self.data is None or self.data.empty:
            return False
        
        # Need at least 1 numeric column
        numeric_cols = [col for col in self.data.columns 
                       if pd.api.types.is_numeric_dtype(self.data[col])]
        
        return len(numeric_cols) >= 1
    
    def set_columns(self, value_column: str, group_column: Optional[str] = None):
        """Set the columns to plot."""
        self.value_column = value_column
        self.group_column = group_column
    
    def set_histogram_params(self, bins: int = 30, density: bool = False,
                           cumulative: bool = False, kde: bool = False,
                           stat: str = 'count'):
        """Set histogram parameters."""
        self.bins = bins
        self.density = density
        self.cumulative = cumulative
        self.kde = kde
        self.stat = stat
    
    def create_plot(self) -> Tuple[plt.Figure, plt.Axes]:
        """Create the histogram."""
        # Create figure
        fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)
        
        # Set default column if not set
        if not self.value_column:
            numeric_cols = [col for col in self.data.columns 
                          if pd.api.types.is_numeric_dtype(self.data[col])]
            if numeric_cols:
                self.value_column = numeric_cols[0]
        
        # Get data
        data_to_plot = self.data[self.value_column].dropna()
        
        # Create histogram based on grouping
        if self.group_column and self.group_column in self.data.columns:
            # Multiple histograms for groups
            groups = self.data[self.group_column].unique()
            # Use config colors if available
            if self.config.color_palette and len(self.config.color_palette) > 0:
                colors = self.config.color_palette
            else:
                from matplotlib import colors as mcolors
                colors_array = plt.cm.tab10(np.linspace(0, 1, len(groups)))
                colors = [mcolors.to_hex(c) for c in colors_array]
            
            for i, group in enumerate(groups):
                group_data = self.data[self.data[self.group_column] == group][self.value_column].dropna()
                
                ax.hist(group_data, bins=self.bins, alpha=0.6, 
                       color=colors[i % len(colors)], label=str(group),
                       density=self.density, cumulative=self.cumulative,
                       edgecolor='black', linewidth=0.5)
        else:
            # Single histogram
            # Use first color from palette if available
            hist_color = self.config.color_palette[0] if self.config.color_palette and len(self.config.color_palette) > 0 else 'steelblue'

            n, bins, patches = ax.hist(data_to_plot, bins=self.bins, 
                                    alpha=0.7, color=hist_color,
                                    density=self.density, 
                                    cumulative=self.cumulative,
                                    edgecolor='black', linewidth=0.5)
            
            # Add KDE if requested
            if self.kde and not self.cumulative:
                from scipy import stats
                kde = stats.gaussian_kde(data_to_plot)
                x_range = np.linspace(data_to_plot.min(), data_to_plot.max(), 200)
                kde_values = kde(x_range)
                
                # Scale KDE to match histogram
                if not self.density:
                    kde_values = kde_values * len(data_to_plot) * (bins[1] - bins[0])
                
                ax2 = ax.twinx()
                ax2.plot(x_range, kde_values, 'r-', linewidth=2, label='KDE')
                ax2.set_ylabel('Density', color='r')
                ax2.tick_params(axis='y', labelcolor='r')
        
        # Add statistics
        mean_val = data_to_plot.mean()
        median_val = data_to_plot.median()
        
        # Add vertical lines for mean and median
        ax.axvline(mean_val, color='red', linestyle='--', linewidth=1.5, 
                  alpha=0.7, label=f'Mean: {mean_val:.2f}')
        ax.axvline(median_val, color='green', linestyle='--', linewidth=1.5,
                  alpha=0.7, label=f'Median: {median_val:.2f}')
        
        # Set labels
        ax.set_xlabel(self.value_column if not self.config.xlabel else self.config.xlabel)
        y_label = 'Density' if self.density else 'Frequency'
        ax.set_ylabel(y_label if not self.config.ylabel else self.config.ylabel)
        
        self.figure = fig
        self.axes = ax
        
        return fig, ax
    
    @classmethod
    def get_required_params(cls):
        """Get required parameters."""
        return {
            'value_column': str,
        }
    
    @classmethod
    def get_optional_params(cls):
        """Get optional parameters."""
        return {
            'group_column': str,
            'bins': int,
            'density': bool,
            'cumulative': bool,
            'kde': bool,
            'stat': str,
        }