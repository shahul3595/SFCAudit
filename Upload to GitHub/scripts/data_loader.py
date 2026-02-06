"""
ULB Audit Framework - Data Loader Module (CORRECTED VERSION - ALL 24 FILES)
Loads and structures all CSV files for processing
"""

import pandas as pd
import os
from pathlib import Path
import logging

class DataLoader:
    """Loads ULB data from CSV files"""
    
    def __init__(self, data_folder):
        self.data_folder = Path(data_folder)
        self.data = {}
        self.ulb_list = []
        self.logger = logging.getLogger(__name__)
        
    def load_all_data(self):
        """Load all CSV files and organize by table name"""
        self.logger.info("Loading data from CSV files...")
        
        # ALL 24 Expected table files based on your complete dataset
        table_files = {
            # Part 1 - Demographics (4 files)
            'p1_1_1_2': 'mp_270126_p1_1_1_2.csv',
            'p1_7': 'mp_270126_p1_7.csv',
            'p1_8': 'mp_270126_p1_8.csv',
            'p1_9': 'mp_270126_p1_9.csv',
            
            # Part 2 - Human Resources (4 files)
            'p2_2_1_1_2_1_5': 'mp_270126_p2_2_1_1_2_1_5.csv',
            'p2_1_6_p2_2_2_4': 'mp_270126_p2_2_1_6_p2_2_2_2_4.csv',
            'p2_2_5': 'mp_270126_p2_2_5.csv',
            'p2_2_6': 'mp_270126_p2_2_6.csv',
            
            # Part 3 - Accounts (1 file)
            'p3': 'mp_270126_p3.csv',
            
            # Part 4 - Taxation & DCB (2 files)
            'p4': 'mp_270126_p4.csv',
            'p4_15_others': 'mp_270126_p4_15_others.csv',
            
            # Part 5 - Liabilities (2 files)
            'p5a': 'mp_270126_p5a.csv',
            'p5b': 'mp_270126_p5b.csv',
            
            # Part 6 - Capital Works (1 file)
            'p6': 'mp_270126_p6.csv',
            
            # Part 7 - Assets (2 files)
            'p7_14': 'mp_270126_p7_14.csv',
            'p7_assets': 'mp_270126_p7_assets.csv',
            
            # Part 8 - Service Levels (1 file)
            'p8': 'mp_270126_p8.csv',
            
            # Part 9 - Future Needs (3 files)
            'p9': 'mp_270126_p9.csv',
            'p9_14_2_a': 'mp_270126_p9_9_14_2_a.csv',
            'p9_14_2_b': 'mp_270126_p9_9_14_2_b.csv',
        }
        
        # Try multiple potential file naming patterns
        loaded_count = 0
        
        # Also check for files without timestamp prefix
        alternative_patterns = [
            'mp_270126_{}.csv',
            '{}.csv',
            'mp_{}.csv'
        ]
        
        for table_name, primary_filename in table_files.items():
            loaded = False
            
            # Try primary filename first
            filepath = self.data_folder / primary_filename
            if filepath.exists():
                try:
                    df = pd.read_csv(filepath, encoding='utf-8-sig')  # Handle BOM
                    if table_name == 'p7_assets':
                        df = self._normalize_commission_year(df)
                    self.data[table_name] = df
                    self.logger.info(f"  [OK] Loaded {table_name}: {len(df)} rows, {len(df.columns)} columns")
                    loaded = True
                    loaded_count += 1
                except Exception as e:
                    self.logger.warning(f"  ✗ Failed to load {primary_filename}: {str(e)}")
            
            # If primary not found, try alternatives
            if not loaded:
                for pattern in alternative_patterns:
                    alt_filename = pattern.format(table_name)
                    alt_filepath = self.data_folder / alt_filename
                    if alt_filepath.exists():
                        try:
                            df = pd.read_csv(alt_filepath, encoding='utf-8-sig')
                            if table_name == 'p7_assets':
                                df = self._normalize_commission_year(df)
                            self.data[table_name] = df
                            self.logger.info(f"  [OK] Loaded {table_name} (from {alt_filename}): {len(df)} rows, {len(df.columns)} columns")
                            loaded = True
                            loaded_count += 1
                            break
                        except Exception as e:
                            self.logger.warning(f"  ✗ Failed to load {alt_filename}: {str(e)}")
            
            if not loaded:
                self.logger.warning(f"  [WARNING] File not found for {table_name} (expected: {primary_filename})")
        
        self.logger.info(f"\n[OK] Successfully loaded {loaded_count} out of {len(table_files)} expected files")
        
        # Extract ULB list from Part 1
        if 'p1_1_1_2' in self.data:
            df_p1 = self.data['p1_1_1_2']
            self.ulb_list = df_p1[['mp_id', 'municipality_name', 'district_name']].to_dict('records')
            self.logger.info(f"[OK] Found {len(self.ulb_list)} ULBs")
        else:
            self.logger.error("✗ Part 1 data not found - cannot extract ULB list")
        
        return self.data

    def _normalize_commission_year(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize commission year values for Part 7 assets."""
        if 'p7_comm_year' not in df.columns:
            return df

        year_series = df['p7_comm_year'].astype(str).str.strip()
        year_series = year_series.replace(r'(?i)^before\s*1990$', '1989', regex=True)
        year_series = year_series.replace(r'(?i)^before1990$', '1989', regex=True)
        year_series = year_series.replace('', pd.NA)
        df['p7_comm_year'] = pd.to_numeric(year_series, errors='coerce')
        return df
    
    def get_ulb_data(self, mp_id, table_name):
        """Get data for specific ULB and table"""
        if table_name not in self.data:
            return None
        
        df = self.data[table_name]
        if 'mp_id' not in df.columns:
            return df  # Return full table if no mp_id column
        
        ulb_data = df[df['mp_id'] == mp_id].copy()
        return ulb_data if not ulb_data.empty else None
    
    def get_ulb_info(self, mp_id):
        """Get basic info for a ULB"""
        for ulb in self.ulb_list:
            if ulb['mp_id'] == mp_id:
                return ulb
        return None
    
    def get_all_ulb_ids(self):
        """Get list of all ULB IDs"""
        return [ulb['mp_id'] for ulb in self.ulb_list]
