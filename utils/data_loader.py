"""Data loading utilities."""

import pandas as pd
from pathlib import Path
from typing import Optional, Union
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
            return cls._infer_datetimes(method(file_path, **kwargs))
        except Exception as e:
            raise ValueError(f"Error loading file: {e}")

    @classmethod
    def _infer_datetimes(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Convert string columns that are overwhelmingly parseable dates.

        CSV/Excel deliver dates as plain strings; without this the temporal
        plots treat them as unordered categorical ticks. Conservative:
        requires >=95% of a sample to parse, and skips numeric-looking
        columns (ids, zip codes) which are not dates.
        """
        for col in df.columns:
            if not (pd.api.types.is_object_dtype(df[col])
                    or pd.api.types.is_string_dtype(df[col])):
                continue
            sample = df[col].dropna().iloc[:1000]
            if sample.empty:
                continue
            if pd.to_numeric(sample, errors='coerce').notna().mean() > 0.5:
                continue
            parsed = pd.to_datetime(sample, errors='coerce', format='mixed')
            if parsed.notna().mean() >= 0.95:
                df[col] = pd.to_datetime(df[col], errors='coerce', format='mixed')
        return df
    
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
                df = pd.read_csv(uploaded_file)
            elif suffix in ['.xlsx', '.xls']:
                df = pd.read_excel(uploaded_file)
            elif suffix == '.json':
                df = pd.read_json(uploaded_file)
            elif suffix == '.parquet':
                df = pd.read_parquet(uploaded_file)
            else:
                st.error(f"Unsupported file format: {suffix}")
                return None
            return cls._infer_datetimes(df)
                
        except Exception as e:
            st.error(f"Error loading file: {e}")
            return None
