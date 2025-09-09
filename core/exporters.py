"""Export functionality for plots."""

import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional, Dict, Any


class PlotExporter:
    """Handle exporting plots to various formats."""
    
    @staticmethod
    def export(figure: plt.Figure, 
               filename: str,
               format: str = 'png',
               dpi: int = 300,
               transparent: bool = False,
               **kwargs) -> Path:
        """Export a plot to file.
        
        Args:
            figure: Matplotlib figure to export
            filename: Output filename (without extension)
            format: Export format (png, pdf, svg, eps)
            dpi: Resolution for raster formats
            transparent: Whether to use transparent background
            **kwargs: Additional arguments for savefig
            
        Returns:
            Path to the exported file
        """
        # Ensure exports directory exists
        from config import settings
        export_dir = settings.EXPORTS_DIR
        export_dir.mkdir(exist_ok=True)
        
        # Create full path
        file_path = export_dir / f"{filename}.{format}"
        
        # Export figure
        figure.savefig(
            file_path,
            format=format,
            dpi=dpi,
            transparent=transparent,
            bbox_inches='tight',
            pad_inches=0.1,
            **kwargs
        )
        
        return file_path