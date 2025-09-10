"""Dynamic plot type registration system."""

from typing import Dict, List, Optional, Type
from pathlib import Path


class PlotRegistry:
    """Registry for all available plot types."""
    
    _instance = None
    _plots: Dict[str, Type] = {}
    _categories: Dict[str, List[str]] = {}
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, category: str, name: Optional[str] = None):
        """Decorator for registering plot types.
        
        Args:
            category: Category of the plot
            name: Optional custom name for the plot
        """
        def decorator(plotter_class):
            instance = cls()
            plot_name = name or plotter_class.__name__.lower().replace('plotter', '')
            plot_id = f"{category}.{plot_name}"
            
            instance._plots[plot_id] = plotter_class
            
            if category not in instance._categories:
                instance._categories[category] = []
            instance._categories[category].append(plot_id)
            
            # Set category on the class
            plotter_class.category = category
            
            return plotter_class
        return decorator
    
    def get_plot(self, plot_id: str) -> Optional[Type]:
        """Get a plot class by ID.
        
        Args:
            plot_id: ID of the plot (e.g., 'temporal.line')
            
        Returns:
            Plot class or None if not found
        """
        return self._plots.get(plot_id)
    
    def get_categories(self) -> List[str]:
        """Get all available categories.
        
        Returns:
            List of category names
        """
        return list(self._categories.keys())
    
    def get_plots_in_category(self, category: str) -> List[str]:
        """Get all plots in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of plot IDs in the category
        """
        return self._categories.get(category, [])
    
    def get_all_plots(self) -> Dict[str, Type]:
        """Get all registered plots.
        
        Returns:
            Dictionary of plot IDs to plot classes
        """
        return self._plots.copy()
    
    def create_plot(self, plot_id: str, data, config=None):
        """Create a plot instance.
        
        Args:
            plot_id: ID of the plot
            data: Data for the plot
            config: Plot configuration
            
        Returns:
            Plot instance or None if plot type not found
        """
        plot_class = self.get_plot(plot_id)
        if plot_class:
            return plot_class(data, config)
        return None
    
    def get_plot_info(self, plot_id: str) -> Dict:
        """Get information about a plot type.
        
        Args:
            plot_id: ID of the plot
            
        Returns:
            Dictionary with plot information
        """
        plot_class = self.get_plot(plot_id)
        if plot_class:
            return {
                'id': plot_id,
                'name': plot_class.name,
                'category': plot_class.category,
                'description': plot_class.description,
                'required_columns': plot_class.required_columns,
                'supports_multiple_series': plot_class.supports_multiple_series,
                'required_params': plot_class.get_required_params(),
                'optional_params': plot_class.get_optional_params(),
            }
        return {}


# Create a global registry instance
plot_registry = PlotRegistry()