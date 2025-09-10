"""Initialize plotters and register them."""

from core.plot_registry import plot_registry

def register_all_plots():
    """Register all available plots."""
    
    # Import and register temporal plots
    try:
        from plotters.temporal.line import LinePlotter
        plot_registry.register("temporal", "line")(LinePlotter)
    except ImportError as e:
        print(f"Failed to register LinePlotter: {e}")
    
    # Import and register categorical plots
    try:
        from plotters.categorical.bar import BarPlotter
        plot_registry.register("categorical", "bar")(BarPlotter)
    except ImportError as e:
        print(f"Failed to register BarPlotter: {e}")
    
    # Import and register statistical plots
    try:
        from plotters.statistical.scatter import ScatterPlotter
        plot_registry.register("statistical", "scatter")(ScatterPlotter)
    except ImportError as e:
        print(f"Failed to register ScatterPlotter: {e}")
    
    try:
        from plotters.statistical.histogram import HistogramPlotter
        plot_registry.register("statistical", "histogram")(HistogramPlotter)
    except ImportError as e:
        print(f"Failed to register HistogramPlotter: {e}")
    
    try:
        from plotters.statistical.boxplot import BoxPlotter
        plot_registry.register("statistical", "boxplot")(BoxPlotter)
    except ImportError as e:
        print(f"Failed to register BoxPlotter: {e}")
    
    try:
        from plotters.statistical.heatmap import HeatmapPlotter
        plot_registry.register("statistical", "heatmap")(HeatmapPlotter)
    except ImportError as e:
        print(f"Failed to register HeatmapPlotter: {e}")

# Register all plots when module is imported
register_all_plots()