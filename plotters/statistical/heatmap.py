"""Heatmap implementation."""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Tuple, Optional
from core.base_plotter import BasePlotter, PlotConfig


class HeatmapPlotter(BasePlotter):
    """Create heatmaps for correlation or matrix visualization."""
    
    name = "Heatmap"
    category = "statistical"
    description = "Visualize matrix data or correlations with color encoding"
    required_columns = 2
    supports_multiple_series = False
    
    def __init__(self, data: pd.DataFrame, config: Optional[PlotConfig] = None):
        """Initialize heatmap plotter."""
        super().__init__(data, config)
        self.value_columns = None
        self.correlation = False
        self.annotate = True
        self.cmap = 'RdBu_r'
        self.vmin = None
        self.vmax = None
        self.fmt = '.2f'
    
    def validate_data(self) -> bool:
        """Validate data for heatmap."""
        if self.data is None or self.data.empty:
            return False
        
        return len(self.data.columns) >= 2
    
    def set_columns(self, value_columns: Optional[List[str]] = None):
        """Set the columns to plot."""
        self.value_columns = value_columns
    
    def set_heatmap_params(self, correlation: bool = False,
                          annotate: bool = True,
                          cmap: str = 'RdBu_r',
                          fmt: str = '.2f'):
        """Set heatmap parameters."""
        self.correlation = correlation
        self.annotate = annotate
        self.cmap = cmap
        self.fmt = fmt
    
    def create_plot(self) -> Tuple[plt.Figure, plt.Axes]:
        """Create the heatmap."""
        # Create figure
        fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)
        
        # Prepare data
        if self.correlation:
            # Correlation matrix
            if self.value_columns:
                numeric_data = self.data[self.value_columns]
            else:
                # Use all numeric columns
                numeric_cols = [col for col in self.data.columns 
                              if pd.api.types.is_numeric_dtype(self.data[col])]
                numeric_data = self.data[numeric_cols]
            
            matrix = numeric_data.corr()
            self.vmin = -1
            self.vmax = 1
        else:
            # Use data as is (assuming it's already a matrix-like structure)
            if self.value_columns:
                matrix = self.data[self.value_columns]
            else:
                # Try to use all numeric columns
                numeric_cols = [col for col in self.data.columns 
                              if pd.api.types.is_numeric_dtype(self.data[col])]
                if numeric_cols:
                    matrix = self.data[numeric_cols]
                else:
                    matrix = self.data
        
        # Create heatmap
        im = ax.imshow(matrix, cmap=self.cmap, aspect='auto',
                      vmin=self.vmin, vmax=self.vmax)
        
        # Set ticks
        ax.set_xticks(np.arange(len(matrix.columns)))
        ax.set_yticks(np.arange(len(matrix.index)))
        ax.set_xticklabels(matrix.columns)
        ax.set_yticklabels(matrix.index)
        
        # Rotate the tick labels
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.ax.set_ylabel('Correlation' if self.correlation else 'Value', rotation=90, va="bottom")
        
        # Add annotations if requested
        if self.annotate:
            for i in range(len(matrix.index)):
                for j in range(len(matrix.columns)):
                    value = matrix.iloc[i, j]
                    if not pd.isna(value):
                        text = ax.text(j, i, format(value, self.fmt),
                                     ha="center", va="center",
                                     color="white" if abs(value) > 0.5 else "black",
                                     fontsize=8)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
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
            'correlation': bool,
            'annotate': bool,
            'cmap': str,
            'fmt': str,
        }