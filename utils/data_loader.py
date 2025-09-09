"""Data loading utilities."""

import pandas as pd
import json
from pathlib import Path
from typing import Optional, Union, Dict, Any
import streamlit as st


class DataLoader:
    """Handle loading data from various formats."""
    
    SUPPORTED_FORMATS = {
        '.csv': 'read_csv',
        '.xlsx': 'read_excel',
        '.xls': 'read_excel',
        '.json': 'read_json',
        '.parquet': 'read_parquet',
    }
    
    @classmethod
    def load_file(cls, file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """Load data from a file.
        
        Args:
            file_path: Path to the file
            **kwargs: Additional arguments for the pandas read function
            
        Returns:
            Loaded DataFrame
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        suffix = file_path.suffix.lower()
        if suffix not in cls.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format: {suffix}")
        
        method_name = cls.SUPPORTED_FORMATS[suffix]
        method = getattr(pd, method_name)
        
        try:
            return method(file_path, **kwargs)
        except Exception as e:
            raise ValueError(f"Error loading file: {e}")
    
    @classmethod
    def load_uploaded_file(cls, uploaded_file) -> Optional[pd.DataFrame]:
        """Load data from a Streamlit uploaded file.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            Loaded DataFrame or None
        """
        if uploaded_file is None:
            return None
        
        try:
            suffix = Path(uploaded_file.name).suffix.lower()
            
            if suffix == '.csv':
                return pd.read_csv(uploaded_file)
            elif suffix in ['.xlsx', '.xls']:
                return pd.read_excel(uploaded_file)
            elif suffix == '.json':
                return pd.read_json(uploaded_file)
            elif suffix == '.parquet':
                return pd.read_parquet(uploaded_file)
            else:
                st.error(f"Unsupported file format: {suffix}")
                return None
                
        except Exception as e:
            st.error(f"Error loading file: {e}")
            return None
    
    @classmethod
    def get_column_info(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Get information about DataFrame columns.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with column information
        """
        info = {}
        for col in df.columns:
            info[col] = {
                'dtype': str(df[col].dtype),
                'nunique': df[col].nunique(),
                'null_count': df[col].isnull().sum(),
                'is_numeric': pd.api.types.is_numeric_dtype(df[col]),
                'is_datetime': pd.api.types.is_datetime64_any_dtype(df[col]),
                'is_categorical': pd.api.types.is_categorical_dtype(df[col]) or df[col].dtype == 'object',
            }
        return info
    
    @classmethod
    def prepare_data(cls, df: pd.DataFrame, 
                    numeric_columns: Optional[list] = None,
                    datetime_columns: Optional[list] = None,
                    categorical_columns: Optional[list] = None) -> pd.DataFrame:
        """Prepare data for plotting.
        
        Args:
            df: DataFrame to prepare
            numeric_columns: Columns to convert to numeric
            datetime_columns: Columns to convert to datetime
            categorical_columns: Columns to convert to categorical
            
        Returns:
            Prepared DataFrame
        """
        df = df.copy()
        
        # Convert numeric columns
        if numeric_columns:
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert datetime columns
        if datetime_columns:
            for col in datetime_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Convert categorical columns
        if categorical_columns:
            for col in categorical_columns:
                if col in df.columns:
                    df[col] = df[col].astype('category')
        
        return df
    
    @classmethod
    def generate_sample_data(cls, plot_type: str, n_points: int = 100) -> pd.DataFrame:
        """Generate sample data for a plot type.
        
        Args:
            plot_type: Type of plot
            n_points: Number of data points
            
        Returns:
            Sample DataFrame
        """
        import numpy as np
        
        if 'line' in plot_type or 'temporal' in plot_type:
            return pd.DataFrame({
                'x': pd.date_range('2024-01-01', periods=n_points, freq='D'),
                'y1': np.cumsum(np.random.randn(n_points)),
                'y2': np.cumsum(np.random.randn(n_points)),
                'y3': np.cumsum(np.random.randn(n_points)),
            })
        
        elif 'scatter' in plot_type:
            return pd.DataFrame({
                'x': np.random.randn(n_points),
                'y': np.random.randn(n_points),
                'size': np.random.uniform(10, 100, n_points),
                'category': np.random.choice(['A', 'B', 'C'], n_points),
            })
        
        elif 'bar' in plot_type or 'categorical' in plot_type:
            categories = [f'Category {i}' for i in range(10)]
            return pd.DataFrame({
                'category': categories,
                'value1': np.random.uniform(10, 100, 10),
                'value2': np.random.uniform(10, 100, 10),
                'value3': np.random.uniform(10, 100, 10),
            })
        
        elif 'histogram' in plot_type:
            return pd.DataFrame({
                'values': np.random.randn(n_points) * 10 + 50,
                'group': np.random.choice(['Group A', 'Group B'], n_points),
            })
        
        else:
            # Default sample data
            return pd.DataFrame({
                'x': range(n_points),
                'y': np.random.randn(n_points),
            })