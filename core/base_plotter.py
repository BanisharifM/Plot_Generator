"""Abstract base class for all plotters."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple, List
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass, field


@dataclass
class PlotConfig:
    """Configuration for a plot."""
    
    title: str = ""
    xlabel: str = ""
    ylabel: str = ""
    figsize: Tuple[float, float] = (3.5, 2.625)
    dpi: int = 300
    style: str = "default"
    color_palette: List[str] = field(default_factory=list)
    grid: bool = True
    legend: bool = True
    legend_loc: str = "best"
    font_size: int = 10
    line_width: float = 1.5
    marker_size: float = 6
    alpha: float = 1.0
    annotations: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary."""
        return {
            k: v for k, v in self.__dict__.items() 
            if not k.startswith('_')
        }


class BasePlotter(ABC):
    """Abstract base class for all plot types."""
    
    # Class attributes to be defined by subclasses
    name: str = "Base Plotter"
    category: str = "general"
    description: str = "Base plotter class"
    required_columns: int = 1
    supports_multiple_series: bool = False
    
    def __init__(self, data: pd.DataFrame, config: Optional[PlotConfig] = None):
        """Initialize the plotter.
        
        Args:
            data: The data to plot
            config: Plot configuration
        """
        self.data = data
        self.config = config or PlotConfig()
        self.figure = None
        self.axes = None
        
    @abstractmethod
    def validate_data(self) -> bool:
        """Validate that the data is suitable for this plot type.
        
        Returns:
            True if data is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def create_plot(self) -> Tuple[plt.Figure, plt.Axes]:
        """Create the plot.
        
        Returns:
            Tuple of (figure, axes)
        """
        pass
    
    def apply_styling(self) -> None:
        """Apply styling to the plot."""
        if self.axes is None:
            return
            
        # Set labels
        if self.config.title:
            self.axes.set_title(self.config.title, fontsize=self.config.font_size + 1)
        if self.config.xlabel:
            self.axes.set_xlabel(self.config.xlabel, fontsize=self.config.font_size)
        if self.config.ylabel:
            self.axes.set_ylabel(self.config.ylabel, fontsize=self.config.font_size)
        
        # Set grid
        if self.config.grid:
            self.axes.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
        # Set legend
        if self.config.legend and self.axes.get_legend_handles_labels()[0]:
            self.axes.legend(loc=self.config.legend_loc, fontsize=self.config.font_size - 1)
        
        # Apply tight layout
        self.figure.tight_layout()
    
    def add_annotations(self) -> None:
        """Add annotations to the plot."""
        if not self.config.annotations or self.axes is None:
            return
            
        for ann in self.config.annotations:
            self.axes.annotate(
                ann.get('text', ''),
                xy=ann.get('xy', (0, 0)),
                xytext=ann.get('xytext', (0, 0)),
                arrowprops=ann.get('arrowprops', None),
                fontsize=ann.get('fontsize', self.config.font_size - 2),
                **ann.get('kwargs', {})
            )
    
    def plot(self) -> Tuple[plt.Figure, plt.Axes]:
        """Main plotting method.
        
        Returns:
            Tuple of (figure, axes)
        """
        # Validate data
        if not self.validate_data():
            raise ValueError(f"Invalid data for {self.name}")
        
        # Create plot
        self.figure, self.axes = self.create_plot()
        
        # Apply styling
        self.apply_styling()
        
        # Add annotations
        self.add_annotations()
        
        return self.figure, self.axes
    
    @classmethod
    def get_required_params(cls) -> Dict[str, Any]:
        """Get required parameters for this plot type.
        
        Returns:
            Dictionary of parameter names and types
        """
        return {
            'x_column': str,
            'y_column': str,
        }
    
    @classmethod
    def get_optional_params(cls) -> Dict[str, Any]:
        """Get optional parameters for this plot type.
        
        Returns:
            Dictionary of parameter names and default values
        """
        return {
            'color': None,
            'size': None,
            'hue': None,
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name='{self.name}', category='{self.category}')"