"""Box plot implementation."""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List
from core.base_plotter import BasePlotter, PlotConfig


class BoxPlotter(BasePlotter):
    """Create box plots for statistical summary."""
    
    name = "Box Plot"
    category = "statistical"
    description = "Display statistical summary with quartiles and outliers"
    required_columns = 1
    supports_multiple_series = True
    
    def __init__(self, data: pd.DataFrame, config: Optional[PlotConfig] = None):
        """Initialize box plotter."""
        super().__init__(data, config)
        self.value_columns = []
        self.group_column = None
        self.orientation = 'vertical'
        self.show_outliers = True
        self.show_means = True
        self.notch = False
    
    def validate_data(self) -> bool:
        """Validate data for box plot."""
        if self.data is None or self.data.empty:
            return False
        
        # Need at least 1 numeric column
        numeric_cols = [col for col in self.data.columns 
                       if pd.api.types.is_numeric_dtype(self.data[col])]
        
        return len(numeric_cols) >= 1
    
    def set_columns(self, value_columns: List[str], group_column: Optional[str] = None):
        """Set the columns to plot."""
        self.value_columns = value_columns if isinstance(value_columns, list) else [value_columns]
        self.group_column = group_column
    
    def set_box_params(self, orientation: str = 'vertical', 
                      show_outliers: bool = True,
                      show_means: bool = True,
                      notch: bool = False):
        """Set box plot parameters."""
        self.orientation = orientation
        self.show_outliers = show_outliers
        self.show_means = show_means
        self.notch = notch
    
    def create_plot(self) -> Tuple[plt.Figure, plt.Axes]:
        """Create the box plot."""
        # Create figure
        fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)
        
        # Set default columns if not set
        if not self.value_columns:
            numeric_cols = [col for col in self.data.columns 
                          if pd.api.types.is_numeric_dtype(self.data[col])]
            self.value_columns = numeric_cols[:min(5, len(numeric_cols))]  # Max 5 columns
        
        # Prepare data for plotting
        if self.group_column and self.group_column in self.data.columns:
            # Grouped box plot
            groups = self.data[self.group_column].unique()
            data_to_plot = []
            labels = []
            
            for col in self.value_columns:
                for group in groups:
                    group_data = self.data[self.data[self.group_column] == group][col].dropna()
                    data_to_plot.append(group_data)
                    labels.append(f"{col}\n{group}")
        else:
            # Simple box plot
            data_to_plot = [self.data[col].dropna() for col in self.value_columns]
            labels = self.value_columns
        
        # Create box plot
        vert = self.orientation == 'vertical'
        bp = ax.boxplot(data_to_plot, 
                       vert=vert,
                       labels=labels,
                       notch=self.notch,
                       showmeans=self.show_means,
                       showfliers=self.show_outliers,
                       patch_artist=True,
                       boxprops=dict(facecolor='lightblue', alpha=0.7),
                       medianprops=dict(color='red', linewidth=2),
                       meanprops=dict(marker='o', markerfacecolor='green', 
                                    markeredgecolor='green', markersize=8),
                       flierprops=dict(marker='o', markerfacecolor='red', 
                                     markersize=5, alpha=0.5))
        
        # Color boxes using config palette if available
        if self.config.color_palette and len(self.config.color_palette) > 0:
            colors = self.config.color_palette
        else:
            colors_array = plt.cm.Set3(np.linspace(0, 1, len(bp['boxes'])))
            from matplotlib import colors as mcolors
            colors = [mcolors.to_hex(c) for c in colors_array]

        for i, patch in enumerate(bp['boxes']):
            patch.set_facecolor(colors[i % len(colors)])
        
        # Add grid
        ax.grid(True, alpha=0.3, axis='y' if vert else 'x')
        
        # Rotate labels if needed
        if vert and len(labels) > 5:
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        self.figure = fig
        self.axes = ax
        
        return fig, ax
    
    @classmethod
    def get_required_params(cls):
        """Get required parameters."""
        return {
            'value_columns': list,
        }
    
    @classmethod
    def get_optional_params(cls):
        """Get optional parameters."""
        return {
            'group_column': str,
            'orientation': str,
            'show_outliers': bool,
            'show_means': bool,
            'notch': bool,
        }