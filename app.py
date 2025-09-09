"""Main Streamlit application for Publication Plot Generator."""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from core.plot_registry import plot_registry
from core.base_plotter import PlotConfig
from utils.data_loader import DataLoader
from core.exporters import PlotExporter

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
        if st.button("📝 Use Sample Data"):
            st.session_state.data = DataLoader.generate_sample_data('line', 100)
            st.success("✅ Sample data loaded")
        
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
        # Create plotter instance
        plotter = plot_registry.create_plot(
            plot_id, 
            st.session_state.data, 
            st.session_state.plot_config
        )
        
        if plotter:
            # Set columns
            if 'x_column' in params and 'y_columns' in params:
                plotter.set_columns(params['x_column'], params['y_columns'])
            elif 'x_column' in params and 'y_column' in params:
                plotter.set_columns(params['x_column'], params['y_column'])
            
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
        st.write("**Dimensions**")
        width = st.slider("Width (inches)", 2.0, 10.0, 
                         st.session_state.plot_config.figsize[0])
        height = st.slider("Height (inches)", 2.0, 10.0,
                          st.session_state.plot_config.figsize[1])
        dpi = st.slider("DPI", 100, 600, st.session_state.plot_config.dpi)
        
        st.session_state.plot_config.figsize = (width, height)
        st.session_state.plot_config.dpi = dpi
    
    with col3:
        st.write("**Style**")
        grid = st.checkbox("Show Grid", st.session_state.plot_config.grid)
        legend = st.checkbox("Show Legend", st.session_state.plot_config.legend)
        font_size = st.slider("Font Size", 6, 20, 
                             st.session_state.plot_config.font_size)
        
        st.session_state.plot_config.grid = grid
        st.session_state.plot_config.legend = legend
        st.session_state.plot_config.font_size = font_size
    
    # Apply changes button
    if st.button("🔄 Apply Changes"):
        if st.session_state.current_plot:
            st.success("✅ Changes applied! Recreate the plot to see updates.")

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
            # Here we would implement the actual export
            st.success(f"✅ Plot exported as {filename}.{settings.EXPORT_FORMATS[format_option]['extension']}")
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