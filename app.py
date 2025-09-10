"""Main Streamlit application for Publication Plot Generator."""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from config import palettes
from core.base_plotter import PlotConfig
from utils.data_loader import DataLoader

# Import plotters to register them
import plotters
from core.plot_registry import plot_registry

# Page config
st.set_page_config(
    page_title=settings.APP_NAME,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'current_plot' not in st.session_state:
    st.session_state.current_plot = None
if 'plot_config' not in st.session_state:
    st.session_state.plot_config = PlotConfig()
if 'selected_palette' not in st.session_state:
    st.session_state.selected_palette = 'default'
if 'plotter_instance' not in st.session_state:
    st.session_state.plotter_instance = None

def main():
    """Main application function."""
    
    # Title
    st.title(f"📊 {settings.APP_NAME}")
    st.markdown(settings.APP_DESCRIPTION)
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Data Management")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload your data file",
            type=['csv', 'xlsx', 'xls', 'json', 'parquet'],
            help="Supported formats: CSV, Excel, JSON, Parquet"
        )
        
        if uploaded_file is not None:
            st.session_state.data = DataLoader.load_uploaded_file(uploaded_file)
            if st.session_state.data is not None:
                st.success(f"✅ Loaded {len(st.session_state.data)} rows")
        
        # Or use sample data
        st.divider()
        st.subheader("📝 Sample Datasets")
        
        sample_options = {
            "Time Series": "examples/time_series.csv",
            "Distribution": "examples/distribution_data.csv",
            "Categorical": "examples/categorical_data.csv",
            "Correlation": "examples/correlation_data.csv",
            "Scaling": "examples/scaling_data.csv"
        }
        
        selected_sample = st.selectbox("Choose sample dataset", list(sample_options.keys()))
        
        if st.button("Load Sample Data"):
            try:
                sample_path = sample_options[selected_sample]
                st.session_state.data = DataLoader.load_file(sample_path)
                st.success(f"✅ Loaded {selected_sample} data")
            except Exception as e:
                # Fallback to generated data
                st.session_state.data = DataLoader.generate_sample_data('line', 100)
                st.success("✅ Generated sample data")
        
        # Data preview
        if st.session_state.data is not None:
            st.divider()
            st.subheader("📋 Data Preview")
            st.write(f"Shape: {st.session_state.data.shape}")
            st.write("Columns:", list(st.session_state.data.columns))
            
            with st.expander("View Data"):
                st.dataframe(st.session_state.data.head(10))
    
    # Main content
    if st.session_state.data is not None:
        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Plot", "⚙️ Customize", "💾 Export", "ℹ️ Help"])
        
        with tab1:
            create_plot_tab()
        
        with tab2:
            customize_plot_tab()
        
        with tab3:
            export_plot_tab()
        
        with tab4:
            help_tab()
    else:
        # Welcome message
        st.info("👈 Please upload a data file or use sample data to get started")
        
        # Quick start guide
        with st.expander("🚀 Quick Start Guide"):
            st.markdown("""
            1. **Upload your data** using the file uploader in the sidebar
            2. **Select a plot type** from the available categories
            3. **Configure your plot** by selecting columns and options
            4. **Customize the appearance** using the style editor
            5. **Export your plot** in various formats (PNG, PDF, SVG)
            """)

def create_plot_tab():
    """Create the plot creation tab."""
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📊 Plot Configuration")
        
        # Get available plot categories
        categories = plot_registry.get_categories()
        
        if categories:
            # Select category
            category = st.selectbox("Select Category", categories)
            
            # Get plots in category
            plots = plot_registry.get_plots_in_category(category)
            plot_names = [p.split('.')[-1] for p in plots]
            
            # Select plot type
            plot_name = st.selectbox("Select Plot Type", plot_names)
            plot_id = f"{category}.{plot_name}"
            
            # Get plot info
            plot_info = plot_registry.get_plot_info(plot_id)
            
            if plot_info:
                st.info(plot_info['description'])
                
                # Column selection
                st.divider()
                columns = list(st.session_state.data.columns)
                
                # Required parameters
                params = {}
                for param, param_type in plot_info['required_params'].items():
                    if 'column' in param:
                        if 'columns' in param:
                            params[param] = st.multiselect(
                                param.replace('_', ' ').title(),
                                columns
                            )
                        else:
                            params[param] = st.selectbox(
                                param.replace('_', ' ').title(),
                                columns
                            )
                            
                # special options for heatmap            
                if plot_id == "statistical.heatmap":
                    use_correlation = st.checkbox("Calculate Correlation Matrix", value=True)
                    params['correlation'] = use_correlation
     
                # Create plot button
                if st.button("🎨 Create Plot", type="primary"):
                    create_plot(plot_id, params)
        else:
            st.warning("No plot types available")
    
    with col2:
        st.subheader("📈 Plot Preview")
        
        # Display plot
        if st.session_state.current_plot is not None:
            st.pyplot(st.session_state.current_plot)
        else:
            st.info("Configure and create a plot to see preview")

def create_plot(plot_id: str, params: dict):
    """Create a plot with given parameters."""
    try:
        # Color palette is already set in plot_config during customization
        # No need to apply it here
        
        # Create plotter instance
        plotter = plot_registry.create_plot(
            plot_id, 
            st.session_state.data, 
            st.session_state.plot_config
        )
        
        if plotter:
            # Store plotter instance for later customization
            st.session_state.plotter_instance = plotter
            
            # Set columns based on plot type
            if 'x_column' in params and 'y_columns' in params:
                plotter.set_columns(params['x_column'], params['y_columns'])
            elif 'x_column' in params and 'y_column' in params:
                plotter.set_columns(params['x_column'], params['y_column'])
            elif 'value_column' in params:
                plotter.set_columns(params['value_column'])
            elif 'value_columns' in params:
                plotter.set_columns(params['value_columns'])
                # For heatmap, also set correlation if present
                if plot_id == "statistical.heatmap" and 'correlation' in params:
                    plotter.set_heatmap_params(correlation=params['correlation'])
            
            # Create plot
            fig, ax = plotter.plot()
            st.session_state.current_plot = fig
            st.success("✅ Plot created successfully!")
        else:
            st.error(f"Failed to create plot: {plot_id}")
    except Exception as e:
        st.error(f"Error creating plot: {str(e)}")
        
def customize_plot_tab():
    """Create the customization tab."""
    st.subheader("🎨 Plot Customization")
    
    # First row: Labels and Colors
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Labels**")
        title = st.text_input("Title", st.session_state.plot_config.title)
        xlabel = st.text_input("X Label", st.session_state.plot_config.xlabel)
        ylabel = st.text_input("Y Label", st.session_state.plot_config.ylabel)
        
        st.session_state.plot_config.title = title
        st.session_state.plot_config.xlabel = xlabel
        st.session_state.plot_config.ylabel = ylabel
    
    with col2:
            st.write("**Color Palettes**")
            
            # Get all palette categories
            all_palettes = palettes.get_all_palette_names()
            
            # Add Custom option to the categories
            palette_options = list(all_palettes.keys()) + ["Custom"]
            
            # Select palette category
            palette_category = st.selectbox(
                "Palette Type",
                palette_options
            )
            
            # Handle custom colors differently
            if palette_category == "Custom":
                # Initialize custom colors in session state if not present
                if 'custom_colors' not in st.session_state:
                    st.session_state.custom_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
                
                # Color pickers for custom palette
                st.write("Choose your colors:")
                custom_colors = []
                cols = st.columns(5)
                for i, col in enumerate(cols):
                    with col:
                        color = col.color_picker(f"C{i+1}", 
                                                st.session_state.custom_colors[i] if i < len(st.session_state.custom_colors) else '#000000',
                                                key=f"color_{i}")
                        custom_colors.append(color)
                
                st.session_state.custom_colors = custom_colors
                st.session_state.selected_palette = 'custom'
                st.session_state.plot_config.color_palette = custom_colors
                colors_to_preview = custom_colors
            else:
                # Select specific palette from category
                palette_name = st.selectbox(
                    "Color Scheme",
                    all_palettes[palette_category]
                )
                
                st.session_state.selected_palette = palette_name
                colors_to_preview = palettes.get_palette(palette_name, 7)
                st.session_state.plot_config.color_palette = colors_to_preview
            
            # Show unified preview for both predefined and custom
            st.write("**Preview:**")
            color_html = " ".join([
                f'<span style="background-color:{c};padding:4px 12px;margin:1px;display:inline-block;border-radius:3px">&nbsp;</span>'
                for c in colors_to_preview[:7]
            ])
            st.markdown(color_html, unsafe_allow_html=True)
    
    with col3:
        st.write("**Style Options**")
        grid = st.checkbox("Show Grid", st.session_state.plot_config.grid)
        legend = st.checkbox("Show Legend", st.session_state.plot_config.legend)
        
        legend_loc = st.selectbox(
            "Legend Location",
            ["best", "upper right", "upper left", "lower left", "lower right", 
             "right", "center left", "center right", "lower center", "upper center", "center"],
            index=0
        )
        
        st.session_state.plot_config.grid = grid
        st.session_state.plot_config.legend = legend
        st.session_state.plot_config.legend_loc = legend_loc
    
    # Second row: Dimensions and Typography
    st.divider()
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.write("**Dimensions**")
        width = st.slider("Width (inches)", 2.0, 10.0,
                        float(st.session_state.plot_config.figsize[0]), step=0.1)
        height = st.slider("Height (inches)", 2.0, 10.0,
                        float(st.session_state.plot_config.figsize[1]), step=0.1)
        dpi = st.slider("DPI", 100, 600, st.session_state.plot_config.dpi)
        
        st.session_state.plot_config.figsize = (width, height)
        st.session_state.plot_config.dpi = dpi
    
    with col5:
        st.write("**Typography**")
        font_size = st.slider("Font Size", 6, 20, 
                             st.session_state.plot_config.font_size)
        line_width = st.slider("Line Width", 0.5, 5.0, 
                               st.session_state.plot_config.line_width, step=0.5)
        marker_size = st.slider("Marker Size", 2, 20,
                               int(st.session_state.plot_config.marker_size))
        
        st.session_state.plot_config.font_size = font_size
        st.session_state.plot_config.line_width = line_width
        st.session_state.plot_config.marker_size = marker_size
    
    with col6:
        st.write("**Advanced**")
        alpha = st.slider("Transparency", 0.1, 1.0, 
                         st.session_state.plot_config.alpha, step=0.1)
        
        # Style presets
        style_preset = st.selectbox(
            "Style Preset",
            ["Default", "IEEE", "Nature", "Science", "Minimal", "Seaborn", "ggplot"]
        )
        
        st.session_state.plot_config.alpha = alpha
        
        if style_preset != "Default":
            apply_style_preset(style_preset)
    
    # Apply changes button
    if st.button("🔄 Apply Changes", type="primary"):
        if st.session_state.current_plot:
            st.success("✅ Changes applied! Recreate the plot to see updates.")

def apply_style_preset(preset: str):
    """Apply a style preset to the plot configuration."""
    presets = {
        "IEEE": {
            "figsize": (3.5, 2.625),
            "dpi": 300,
            "font_size": 9,
            "grid": True,
            "legend": True,
        },
        "Nature": {
            "figsize": (3.5, 3.5),
            "dpi": 300,
            "font_size": 8,
            "grid": False,
            "legend": True,
        },
        "Science": {
            "figsize": (3.5, 2.8),
            "dpi": 300,
            "font_size": 9,
            "grid": True,
            "legend": True,
        },
        "Minimal": {
            "figsize": (6, 4),
            "dpi": 150,
            "font_size": 10,
            "grid": False,
            "legend": False,
        }
    }
    
    if preset in presets:
        for key, value in presets[preset].items():
            setattr(st.session_state.plot_config, key, value)

def export_plot_tab():
    """Create the export tab."""
    st.subheader("💾 Export Options")
    
    if st.session_state.current_plot is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Export Settings**")
            format_option = st.selectbox(
                "File Format",
                list(settings.EXPORT_FORMATS.keys())
            )
            
            filename = st.text_input("Filename (without extension)", "plot")
            
        with col2:
            st.write("**Quality Settings**")
            export_dpi = st.slider("Export DPI", 100, 600, 300)
            transparent = st.checkbox("Transparent Background", False)
        
        if st.button("📥 Export Plot", type="primary"):
            try:
                from core.exporters import PlotExporter
                ext = settings.EXPORT_FORMATS[format_option]['extension']
                path = PlotExporter.export(
                    st.session_state.current_plot,
                    filename,
                    format=ext.replace('.', ''),
                    dpi=export_dpi,
                    transparent=transparent
                )
                st.success(f"✅ Plot exported as {filename}{ext}")
                st.info(f"Saved to: {path}")
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
    else:
        st.info("Please create a plot first before exporting")

def help_tab():
    """Create the help tab."""
    st.subheader("ℹ️ Help & Documentation")
    
    st.markdown("""
    ### Available Plot Types
    
    **Temporal Plots**
    - Line Plot: Display trends over time
    - Area Plot: Show cumulative values
    - Timeline: Event-based visualization
    
    **Categorical Plots**
    - Bar Chart: Compare values across categories
    - Grouped Bar: Multiple series comparison
    - Stacked Bar: Part-to-whole relationships
    
    **Statistical Plots**
    - Scatter Plot: Relationship between variables
    - Histogram: Distribution of values
    - Box Plot: Statistical summary
    - Heatmap: Correlation matrices
    
    ### Color Palettes
    
    **Colorblind Safe**: Optimized for accessibility
    **Scientific Journals**: Nature, Science, IEEE standards
    **Categorical**: For discrete categories
    **Sequential**: For continuous values
    **Diverging**: For data with a meaningful center
    
    ### Tips for Publication-Quality Plots
    
    1. **Use appropriate figure sizes**:
       - Single column: 3.5 inches wide
       - Double column: 7.16 inches wide
    
    2. **Ensure readability**:
       - Font size: 9-10 points minimum
       - Line width: 1-2 points
       - High DPI: 300+ for print
    
    3. **Accessibility**:
       - Use colorblind-safe palettes
       - Add patterns or markers in addition to colors
       - Include clear labels and legends
    """)

if __name__ == "__main__":
    main()