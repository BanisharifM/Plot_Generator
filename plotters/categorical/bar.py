"""Bar chart implementation."""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List
from core.base_plotter import BasePlotter, PlotConfig


class BarPlotter(BasePlotter):
    """Create bar charts for categorical data."""
    
    name = "Bar Chart"
    category = "categorical"
    description = "Compare values across categories"
    required_columns = 2
    supports_multiple_series = True
    
    def __init__(self, data: pd.DataFrame, config: Optional[PlotConfig] = None):
        """Initialize bar plotter."""
        super().__init__(data, config)
        self.x_column = None
        self.y_columns = []
        self.orientation = 'vertical'
        self.bar_width = 0.8
        self.grouped = False
        self.stacked = False
    
    def validate_data(self) -> bool:
        """Validate data for bar chart."""
        if self.data is None or self.data.empty:
            return False
        
        # Need at least 2 columns
        if len(self.data.columns) < 2:
            return False
        
        return True
    
    def set_columns(self, x_column: str, y_columns: List[str]):
        """Set the columns to plot."""
        self.x_column = x_column
        self.y_columns = y_columns if isinstance(y_columns, list) else [y_columns]
    
    def set_bar_style(self, orientation: str = 'vertical', 
                     grouped: bool = False, 
                     stacked: bool = False,
                     bar_width: float = 0.8):
        """Set bar chart style."""
        self.orientation = orientation
        self.grouped = grouped
        self.stacked = stacked
        self.bar_width = bar_width
    
    def create_plot(self) -> Tuple[plt.Figure, plt.Axes]:
        """Create the bar chart."""
        # Create figure
        fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)
        
        # Set default columns if not set
        if not self.x_column or not self.y_columns:
            self.x_column = self.data.columns[0]
            self.y_columns = [col for col in self.data.columns[1:] 
                            if pd.api.types.is_numeric_dtype(self.data[col])]
        
        x = np.arange(len(self.data[self.x_column]))
        
        if self.stacked:
            # Stacked bar chart
            bottom = np.zeros(len(x))
            colors = plt.cm.tab10(np.linspace(0, 1, len(self.y_columns)))
            
            for i, y_col in enumerate(self.y_columns):
                if self.orientation == 'vertical':
                    ax.bar(x, self.data[y_col], self.bar_width, 
                          bottom=bottom, label=y_col, color=colors[i])
                    bottom += self.data[y_col]
                else:
                    ax.barh(x, self.data[y_col], self.bar_width, 
                           left=bottom, label=y_col, color=colors[i])
                    bottom += self.data[y_col]
        
        elif self.grouped:
            # Grouped bar chart
            n_groups = len(self.y_columns)
            width = self.bar_width / n_groups
            colors = plt.cm.tab10(np.linspace(0, 1, n_groups))
            
            for i, y_col in enumerate(self.y_columns):
                offset = width * (i - n_groups/2 + 0.5)
                if self.orientation == 'vertical':
                    ax.bar(x + offset, self.data[y_col], width, 
                          label=y_col, color=colors[i])
                else:
                    ax.barh(x + offset, self.data[y_col], width, 
                           label=y_col, color=colors[i])
        
        else:
            # Simple bar chart
            if len(self.y_columns) == 1:
                if self.orientation == 'vertical':
                    ax.bar(x, self.data[self.y_columns[0]], self.bar_width,
                          label=self.y_columns[0])
                else:
                    ax.barh(x, self.data[self.y_columns[0]], self.bar_width,
                           label=self.y_columns[0])
            else:
                # Default to grouped if multiple columns
                self.grouped = True
                return self.create_plot()
        
        # Set x-axis labels
        if self.orientation == 'vertical':
            ax.set_xticks(x)
            ax.set_xticklabels(self.data[self.x_column], rotation=45, ha='right')
        else:
            ax.set_yticks(x)
            ax.set_yticklabels(self.data[self.x_column])
        
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
            'orientation': str,
            'grouped': bool,
            'stacked': bool,
            'bar_width': float,
            'colors': list,
            'error_bars': bool,
        }