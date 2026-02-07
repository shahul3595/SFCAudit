"""
ULB Audit Framework - Rule Executor with Phase 4 Statistical Support
Supports:
- Threshold validation (existing)
- Cross-table validation (existing)
- IQR outlier detection (NEW)
- Z-score outlier detection (NEW)
- Peer grouping: population_size, district, municipality_grade, statewide (NEW)
"""

import pandas as pd
import numpy as np
import logging
import re
from typing import Dict, Any, Optional, List, Set, Tuple

class CalculationEngine:
    """Handles complex calculations for validation rules"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def _is_numeric_column(self, col_spec: str, data: pd.DataFrame) -> bool:
        """Check if a column contains numeric data"""
        if pd.isna(col_spec):
            return False
        
        col_spec = str(col_spec).strip()
        
        # Try as constant first
        try:
            float(col_spec)
            return True
        except:
            pass
        
        # Check if column exists
        if col_spec not in data.columns:
            return False
        
        # Check column data type
        col_data = data[col_spec]
        
        # If already numeric type, return True
        if pd.api.types.is_numeric_dtype(col_data):
            return True
        
        # Try to see if values can be converted to numeric
        non_null_values = col_data.dropna()
        if len(non_null_values) == 0:
            return False
        
        sample_value = non_null_values.iloc[0]
        try:
            float(sample_value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _get_column_value(self, col_spec: str, data: pd.DataFrame, support_sum: bool = True) -> tuple[Optional[float], Optional[str]]:
        """Extract numeric value from column specification"""
        if pd.isna(col_spec):
            return None, "Column specification is missing"
        
        col_spec = str(col_spec).strip()
        
        # Try as constant first
        try:
            return float(col_spec), None
        except:
            pass
        
        # Handle comma-separated columns
        if ',' in col_spec:
            cols = [c.strip() for c in col_spec.split(',')]
            total = 0
            found_any = False
            missing_cols = []
            non_numeric_cols = []
            
            for col in cols:
                if col not in data.columns:
                    missing_cols.append(col)
                    continue
                
                if not self._is_numeric_column(col, data):
                    non_numeric_cols.append(col)
                    continue
                
                if support_sum:
                    col_sum = pd.to_numeric(data[col], errors='coerce').sum()
                    if pd.notna(col_sum):
                        total += float(col_sum)
                        found_any = True
                else:
                    val = pd.to_numeric(data[col].iloc[0], errors='coerce')
                    if pd.notna(val):
                        total += float(val)
                        found_any = True
            
            if non_numeric_cols:
                return None, f"Non-numeric columns: {', '.join(non_numeric_cols)} (contains text/categorical data)"
            if missing_cols:
                return None, f"Missing columns: {', '.join(missing_cols)}"
            if not found_any:
                return None, f"All columns have null values"
            return total, None
        
        # Single column
        if col_spec not in data.columns:
            return None, f"Column '{col_spec}' not found"
        
        if not self._is_numeric_column(col_spec, data):
            return None, f"Column '{col_spec}' contains non-numeric data (text/categorical)"
        
        if support_sum and len(data) > 1:
            col_sum = pd.to_numeric(data[col_spec], errors='coerce').sum()
            if pd.notna(col_sum):
                return float(col_sum), None
            return None, f"Column '{col_spec}' has only null values"
        else:
            val = pd.to_numeric(data[col_spec].iloc[0], errors='coerce')
            if pd.notna(val):
                return float(val), None
            return None, f"Column '{col_spec}' has null value"
    
    def calculate(self, calc_type: str, rule: pd.Series, ulb_data: pd.DataFrame) -> tuple[Optional[float], Optional[str]]:
        """Perform calculation based on type"""
        calc_type = str(calc_type).lower().strip()
        
        if calc_type == 'none' or pd.isna(calc_type):
            return None, None
        
        try:
            if calc_type == 'ratio':
                return self._calc_ratio(rule, ulb_data)
            elif calc_type == 'percentage' or calc_type == 'percentage_of':
                return self._calc_percentage(rule, ulb_data)
            elif calc_type == 'sum':
                return self._calc_sum(rule, ulb_data)
            elif calc_type == 'difference':
                return self._calc_difference(rule, ulb_data)
            elif calc_type == 'cagr':
                return self._calc_cagr(rule, ulb_data)
            elif calc_type == 'growth_rate':
                return self._calc_growth_rate(rule, ulb_data)
            else:
                return None, f"Unknown calculation type: {calc_type}"
        except Exception as e:
            return None, f"Calculation error ({calc_type}): {str(e)}"
    
    def _calc_ratio(self, rule: pd.Series, ulb_data: pd.DataFrame) -> tuple[Optional[float], Optional[str]]:
        val1, err1 = self._get_column_value(rule['column_1'], ulb_data)
        if err1:
            return None, f"Numerator: {err1}"
        val2, err2 = self._get_column_value(rule['column_2'], ulb_data)
        if err2:
            return None, f"Denominator: {err2}"
        if val2 == 0:
            return None, "Division by zero"
        return val1 / val2, None
    
    def _calc_percentage(self, rule: pd.Series, ulb_data: pd.DataFrame) -> tuple[Optional[float], Optional[str]]:
        val1, err1 = self._get_column_value(rule['column_1'], ulb_data)
        if err1:
            return None, f"Numerator: {err1}"
        val2, err2 = self._get_column_value(rule['column_2'], ulb_data)
        if err2:
            return None, f"Denominator: {err2}"
        if val2 == 0:
            return None, "Division by zero"
        return (val1 / val2) * 100, None
    
    def _calc_sum(self, rule: pd.Series, ulb_data: pd.DataFrame) -> tuple[Optional[float], Optional[str]]:
        """Sum multiple columns"""
        total = 0
        cols_used = []
        for col_key in ['column_1', 'column_2', 'column_3', 'column_4']:
            if pd.notna(rule.get(col_key)):
                val, err = self._get_column_value(rule[col_key], ulb_data)
                if err:
                    return None, f"{col_key}: {err}"
                total += val
                cols_used.append(col_key)
        
        if not cols_used:
            return None, "No columns specified for sum"
        return total, None
    
    def _calc_difference(self, rule: pd.Series, ulb_data: pd.DataFrame) -> tuple[Optional[float], Optional[str]]:
        """Calculate difference between two values"""
        val1, err1 = self._get_column_value(rule['column_1'], ulb_data)
        if err1:
            return None, f"First value: {err1}"
        val2, err2 = self._get_column_value(rule['column_2'], ulb_data)
        if err2:
            return None, f"Second value: {err2}"
        return val1 - val2, None
    
    def _calc_cagr(self, rule: pd.Series, ulb_data: pd.DataFrame) -> tuple[Optional[float], Optional[str]]:
        val_final, err1 = self._get_column_value(rule['column_1'], ulb_data)
        if err1:
            return None, f"Final value: {err1}"
        val_initial, err2 = self._get_column_value(rule['column_2'], ulb_data)
        if err2:
            return None, f"Initial value: {err2}"
        if val_initial <= 0 or val_final <= 0:
            return None, "Values must be positive for CAGR"
        years = 14
        if pd.notna(rule.get('time_period')):
            try:
                years = int(''.join(filter(str.isdigit, str(rule['time_period']))))
            except:
                pass
        cagr = (pow(val_final / val_initial, 1 / years) - 1) * 100
        return cagr, None
    
    def _calc_growth_rate(self, rule: pd.Series, ulb_data: pd.DataFrame) -> tuple[Optional[float], Optional[str]]:
        val_final, err1 = self._get_column_value(rule['column_1'], ulb_data)
        if err1:
            return None, f"Final value: {err1}"
        val_initial, err2 = self._get_column_value(rule['column_2'], ulb_data)
        if err2:
            return None, f"Initial value: {err2}"
        if val_initial == 0:
            return None, "Initial value cannot be zero"
        growth = ((val_final - val_initial) / val_initial) * 100
        return growth, None


class ThresholdChecker:
    """Validates values against threshold specifications"""
    
    def check_threshold(self, value: float, threshold_spec: str, rule: pd.Series) -> tuple[bool, str]:
        threshold_spec = str(threshold_spec).strip()
        operator = str(rule.get('operator', '')).strip().lower()
        
        if operator == 'between':
            return self._check_between(value, threshold_spec)
        
        try:
            threshold = float(threshold_spec)
            if operator in ['>', 'gt']:
                return value > threshold, f"{value:.2f} not > {threshold}"
            elif operator in ['<', 'lt']:
                return value < threshold, f"{value:.2f} not < {threshold}"
            elif operator in ['>=', 'gte']:
                return value >= threshold, f"{value:.2f} not >= {threshold}"
            elif operator in ['<=', 'lte']:
                return value <= threshold, f"{value:.2f} not <= {threshold}"
            elif operator in ['==', '=', 'eq']:
                tolerance = max(abs(threshold) * 0.01, 0.01)
                return abs(value - threshold) <= tolerance, f"{value:.2f} != {threshold}"
            elif operator in ['!=', 'neq']:
                tolerance = max(abs(threshold) * 0.01, 0.01)
                return abs(value - threshold) > tolerance, f"{value:.2f} == {threshold}"
            else:
                return True, ""
        except ValueError:
            return True, f"Invalid threshold: {threshold_spec}"
    
    def _check_between(self, value: float, threshold_spec: str) -> tuple[bool, str]:
        try:
            parts = threshold_spec.split('|')
            if len(parts) != 2:
                return True, f"Invalid 'between' format: {threshold_spec}"
            
            lower = float(parts[0].strip())
            upper = float(parts[1].strip())
            
            if lower <= value <= upper:
                return True, ""
            else:
                return False, f"{value:.2f} not in range [{lower}, {upper}]"
        except ValueError:
            return True, f"Invalid 'between' values: {threshold_spec}"


class StatisticalEngine:
    """Handles statistical outlier detection and peer comparison (Phase 4)"""
    
    def __init__(self, data_loader, calc_engine):
        self.data_loader = data_loader
        self.calc_engine = calc_engine
        self.logger = logging.getLogger(__name__)
    
    def extract_municipality_grade(self, ulb_name: str) -> Optional[str]:
        """Extract municipality grade from ULB name"""
        if pd.isna(ulb_name):
            return None
        
        ulb_name = str(ulb_name).upper()
        
        # Pattern 1: "GRADE I", "GRADE II", etc.
        match = re.search(r'GRADE\s+([IVX]+)', ulb_name)
        if match:
            return f"Grade {match.group(1)}"
        
        # Pattern 2: "Selection Grade", "Special Grade"
        match = re.search(r'(SELECTION|SPECIAL)\s+GRADE', ulb_name)
        if match:
            return f"{match.group(1).capitalize()} Grade"
        
        # Pattern 3: "Municipal Corporation"
        if 'CORPORATION' in ulb_name:
            return "Municipal Corporation"
        
        # Default: Check if "Municipality" exists, classify as generic
        if 'MUNICIPALITY' in ulb_name:
            return "Municipality (Unclassified)"
        
        return None
    
    def group_ulbs_by_peer_criteria(self, rule: pd.Series) -> Dict[str, List[str]]:
        """Group ULBs based on peer_group_by setting"""
        peer_group_by = str(rule.get('peer_group_by', 'none')).lower().strip()
        
        if peer_group_by == 'population_size':
            return self._group_by_population(rule)
        elif peer_group_by == 'district':
            return self._group_by_district()
        elif peer_group_by == 'municipality_grade':
            return self._group_by_municipality_grade()
        else:  # 'none' or null
            all_ulb_ids = self.data_loader.get_all_ulb_ids()
            return {'statewide': all_ulb_ids}
    
    def _group_by_population(self, rule: pd.Series) -> Dict[str, List[str]]:
        """Group ULBs by population range"""
        pop_min = rule.get('peer_population_min')
        pop_max = rule.get('peer_population_max')
        
        if pd.isna(pop_min) or pd.isna(pop_max):
            self.logger.warning(f"Population bounds missing for rule {rule['checkpoint_id']}, using statewide")
            all_ulb_ids = self.data_loader.get_all_ulb_ids()
            return {'statewide': all_ulb_ids}
        
        pop_min = float(pop_min)
        pop_max = float(pop_max)
        
        # Get population data from Part 1
        if 'p1_1_1_2' not in self.data_loader.data:
            self.logger.error("Part 1 data not found for population grouping")
            return {}
        
        df_p1 = self.data_loader.data['p1_1_1_2']
        pop_col = 'p1_1_3_4_tot_25_no'
        
        if pop_col not in df_p1.columns:
            self.logger.error(f"Population column '{pop_col}' not found")
            return {}
        
        # Filter ULBs in population range
        df_filtered = df_p1[
            (pd.to_numeric(df_p1[pop_col], errors='coerce') >= pop_min) &
            (pd.to_numeric(df_p1[pop_col], errors='coerce') <= pop_max)
        ]
        
        ulb_ids = df_filtered['mp_id'].tolist()
        group_name = f"pop_{int(pop_min/1000)}k-{int(pop_max/1000)}k"
        
        return {group_name: ulb_ids}
    
    def _group_by_district(self) -> Dict[str, List[str]]:
        """Group ULBs by district"""
        if 'p1_1_1_2' not in self.data_loader.data:
            self.logger.error("Part 1 data not found for district grouping")
            return {}
        
        df_p1 = self.data_loader.data['p1_1_1_2']
        
        if 'district_name' not in df_p1.columns:
            self.logger.error("district_name column not found")
            return {}
        
        groups = {}
        for district in df_p1['district_name'].dropna().unique():
            ulb_ids = df_p1[df_p1['district_name'] == district]['mp_id'].tolist()
            groups[str(district)] = ulb_ids
        
        return groups
    
    def _group_by_municipality_grade(self) -> Dict[str, List[str]]:
        """Group ULBs by municipality grade"""
        if 'p1_1_1_2' not in self.data_loader.data:
            self.logger.error("Part 1 data not found for grade grouping")
            return {}
        
        df_p1 = self.data_loader.data['p1_1_1_2']
        
        grade_col = 'p1_1_1_2_grade'

        if grade_col not in df_p1.columns:
            self.logger.error(f"{grade_col} column not found for grade grouping")
            return {}

        groups = {}
        for _, row in df_p1.iterrows():
            grade = row[grade_col]
            if pd.notna(grade):
                grade = str(grade).strip()
                groups.setdefault(grade, []).append(row['mp_id'])
            if grade:
                if grade not in groups:
                    groups[grade] = []
                groups[grade].append(row['mp_id'])
        
        return groups
    
    def collect_metrics_for_rule(self, rule: pd.Series) -> Dict[str, Optional[float]]:
        """Collect metric values across all ULBs for a statistical rule"""
        metrics = {}
        
        for mp_id in self.data_loader.get_all_ulb_ids():
            ulb_data = self._get_ulb_data_for_rule(mp_id, rule)
            if ulb_data is None or ulb_data.empty:
                metrics[mp_id] = None
                continue
            
            # Calculate metric
            metric_value = self._calculate_metric(rule, ulb_data, mp_id)
            metrics[mp_id] = metric_value
        
        return metrics
    
    def _get_ulb_data_for_rule(self, mp_id: str, rule: pd.Series) -> Optional[pd.DataFrame]:
        """Get ULB data considering multi-part rules"""
        primary_table = rule.get('primary_table')
        if pd.isna(primary_table):
            return None
        
        # Extract table name from full name (e.g., mp_270126_p1_1_1_2 -> p1_1_1_2)
        if str(primary_table).startswith('mp_'):
            parts = str(primary_table).split('_')
            if len(parts) > 2:
                primary_table = '_'.join(parts[2:])
        
        return self.data_loader.get_ulb_data(mp_id, primary_table)
    
    def _calculate_metric(self, rule: pd.Series, ulb_data: pd.DataFrame, mp_id: str) -> Optional[float]:
        """Calculate metric value for a ULB"""
        calc_type = rule.get('calculation_type')
        
        # Handle multi-part rules (need to fetch reference data)
        if str(rule.get('multi_part', 'No')).lower() == 'yes':
            ulb_data = self._merge_multi_part_data(mp_id, rule, ulb_data)
            if ulb_data is None:
                return None
        
        if pd.notna(calc_type) and str(calc_type).lower().strip() != 'none':
            value, error_msg = self.calc_engine.calculate(calc_type, rule, ulb_data)
            if error_msg:
                return None
            return value
        else:
            # Direct column value
            value, error_msg = self.calc_engine._get_column_value(rule['column_1'], ulb_data)
            if error_msg:
                return None
            return value
    
    def _merge_multi_part_data(self, mp_id: str, rule: pd.Series, primary_data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Merge data from multiple parts for calculation"""
        ref_part = rule.get('reference_part')
        ref_table = rule.get('reference_table')
        
        if pd.isna(ref_table):
            return primary_data
        
        # Extract table name
        if str(ref_table).startswith('mp_'):
            parts = str(ref_table).split('_')
            if len(parts) > 2:
                ref_table = '_'.join(parts[2:])
        
        ref_data = self.data_loader.get_ulb_data(mp_id, ref_table)
        if ref_data is None or ref_data.empty:
            return None
        
        # Merge on mp_id if both have it, otherwise assume single-row tables
        if 'mp_id' in primary_data.columns and 'mp_id' in ref_data.columns:
            merged = pd.merge(primary_data, ref_data, on='mp_id', how='left', suffixes=('', '_ref'))
        else:
            # For single-row tables, just concatenate columns
            merged = pd.concat([primary_data.reset_index(drop=True), ref_data.reset_index(drop=True)], axis=1)
        
        return merged
    
    def calculate_iqr_bounds(self, values: List[float], multiplier: float = 1.5) -> Dict[str, float]:
        """Calculate IQR-based outlier bounds"""
        values_array = np.array([v for v in values if v is not None])
        
        if len(values_array) < 4:  # Need at least 4 values for quartiles
            return None
        
        q1 = np.percentile(values_array, 25)
        q3 = np.percentile(values_array, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - (multiplier * iqr)
        upper_bound = q3 + (multiplier * iqr)
        
        return {
            'q1': q1,
            'q3': q3,
            'iqr': iqr,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'multiplier': multiplier,
            'n': len(values_array)
        }
    
    def calculate_zscore_bounds(self, values: List[float], stddev_limit: float = 2.0) -> Dict[str, float]:
        """Calculate Z-score based outlier bounds"""
        values_array = np.array([v for v in values if v is not None])
        
        if len(values_array) < 3:  # Need at least 3 values for meaningful stats
            return None
        
        mean = np.mean(values_array)
        std = np.std(values_array, ddof=1)  # Sample standard deviation
        
        lower_bound = mean - (stddev_limit * std)
        upper_bound = mean + (stddev_limit * std)
        
        return {
            'mean': mean,
            'std': std,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'stddev_limit': stddev_limit,
            'n': len(values_array)
        }
    
    def evaluate_statistical_rule(self, rule: pd.Series) -> List[Dict[str, Any]]:
        """Evaluate a statistical rule across all ULBs"""
        self.logger.info(f"  Evaluating statistical rule: {rule['checkpoint_id']} - {rule['description']}")
        
        # Collect metrics
        all_metrics = self.collect_metrics_for_rule(rule)
        
        # Group ULBs
        peer_groups = self.group_ulbs_by_peer_criteria(rule)
        
        if not peer_groups:
            self.logger.warning(f"  No peer groups found for rule {rule['checkpoint_id']}")
            return []
        
        findings = []
        validation_type = str(rule['validation_type']).lower().strip()
        
        for group_name, ulb_ids in peer_groups.items():
            # Get metrics for this group
            group_metrics = {uid: all_metrics.get(uid) for uid in ulb_ids if all_metrics.get(uid) is not None}
            
            if len(group_metrics) < 3:
                self.logger.warning(f"  Insufficient data for group '{group_name}' ({len(group_metrics)} ULBs), skipping")
                continue
            
            # Calculate bounds
            if validation_type == 'outlier_iqr':
                multiplier = float(rule.get('iqr_multiplier', 1.5))
                bounds = self.calculate_iqr_bounds(list(group_metrics.values()), multiplier)
            elif validation_type == 'outlier_zscore':
                stddev_limit = float(rule.get('stddev_limit', 2.0))
                bounds = self.calculate_zscore_bounds(list(group_metrics.values()), stddev_limit)
            else:
                self.logger.error(f"  Unknown statistical validation type: {validation_type}")
                continue
            
            if bounds is None:
                self.logger.warning(f"  Could not calculate bounds for group '{group_name}'")
                continue
            
            # Evaluate each ULB in the group
            for mp_id in ulb_ids:
                metric_value = all_metrics.get(mp_id)
                if metric_value is None:
                    continue
                
                # Check if outlier
                is_outlier = (metric_value < bounds['lower_bound']) or (metric_value > bounds['upper_bound'])
                
                if is_outlier:
                    finding = self._create_statistical_finding(
                        mp_id, rule, metric_value, bounds, group_name, validation_type
                    )
                    findings.append(finding)
        
        self.logger.info(f"  [OK] Found {len(findings)} statistical outliers")
        return findings
    
    def _create_statistical_finding(self, mp_id: str, rule: pd.Series, value: float, 
                                    bounds: Dict, group_name: str, validation_type: str) -> Dict[str, Any]:
        """Create a finding for statistical outlier"""
        ulb_info = self.data_loader.get_ulb_info(mp_id)
        severity = str(rule['severity']).capitalize() if pd.notna(rule.get('severity')) else 'Medium'
        
        # Determine if above or below bounds
        if value < bounds['lower_bound']:
            position = "below lower bound"
            bound_value = bounds['lower_bound']
        else:
            position = "above upper bound"
            bound_value = bounds['upper_bound']
        
        # Create detailed message based on method
        if validation_type == 'outlier_iqr':
            detail = (f"Value {value:.2f} is {position} {bound_value:.2f} "
                     f"(IQR method, multiplier={bounds['multiplier']}, "
                     f"Q1={bounds['q1']:.2f}, Q3={bounds['q3']:.2f}, IQR={bounds['iqr']:.2f}, "
                     f"peer group: {group_name}, N={bounds['n']})")
        else:  # zscore
            z_score = (value - bounds['mean']) / bounds['std'] if bounds['std'] > 0 else 0
            detail = (f"Value {value:.2f} is {position} {bound_value:.2f} "
                     f"(Z-score method, z={z_score:.2f}, limit={bounds['stddev_limit']}, "
                     f"mean={bounds['mean']:.2f}, std={bounds['std']:.2f}, "
                     f"peer group: {group_name}, N={bounds['n']})")
        
        # Add statistical context if available
        if pd.notna(rule.get('statistical_context')):
            detail += f" | Context: {rule['statistical_context']}"
        
        return {
            'mp_id': mp_id,
            'ulb_name': ulb_info['municipality_name'] if ulb_info else f'ID{mp_id}',
            'district': ulb_info['district_name'] if ulb_info else '',
            'rule_id': rule['checkpoint_id'],
            'part_no': str(rule.get('part', '')),
            'severity': severity,
            'check_type': validation_type,
            'description': rule['description'],
            'detail': detail
        }


class RuleExecutor:
    """Main rule execution engine with Phase 4 statistical support"""
    
    def __init__(self, rules_df: pd.DataFrame, data_loader):
        self.rules_df = rules_df
        self.data_loader = data_loader
        self.calc_engine = CalculationEngine()
        self.threshold_checker = ThresholdChecker()
        self.statistical_engine = StatisticalEngine(data_loader, self.calc_engine)
        self.logger = logging.getLogger(__name__)
        self.logged_errors: Set[str] = set()
    
    def _log_unique_error(self, error_key: str, message: str):
        """Log error only once per unique key"""
        if error_key not in self.logged_errors:
            self.logger.warning(message)
            self.logged_errors.add(error_key)
    
    def execute_all_ulbs(self) -> List[Dict[str, Any]]:
        """Execute all enabled rules across all ULBs"""
        all_findings = []
        enabled_rules = self.rules_df[self.rules_df['enabled'] == True]
        
        self.logger.info(f"\nExecuting {len(enabled_rules)} enabled rules...")
        
        # Separate statistical and threshold rules
        statistical_rules = enabled_rules[
            enabled_rules['validation_type'].isin(['outlier_iqr', 'outlier_zscore'])
        ]
        threshold_rules = enabled_rules[
            ~enabled_rules['validation_type'].isin(['outlier_iqr', 'outlier_zscore'])
        ]
        
        # Execute threshold/cross-table rules (existing logic)
        if len(threshold_rules) > 0:
            self.logger.info(f"\n[1/2] Executing {len(threshold_rules)} threshold/cross-table rules...")
            for _, rule in threshold_rules.iterrows():
                findings = self._execute_threshold_rule_all_ulbs(rule)
                all_findings.extend(findings)
        
        # Execute statistical rules (new Phase 4 logic)
        if len(statistical_rules) > 0:
            self.logger.info(f"\n[2/2] Executing {len(statistical_rules)} statistical rules...")
            for _, rule in statistical_rules.iterrows():
                findings = self.statistical_engine.evaluate_statistical_rule(rule)
                all_findings.extend(findings)
        
        self.logger.info(f"\n[OK] Total findings across all rules: {len(all_findings)}")
        return all_findings
    
    def _execute_threshold_rule_all_ulbs(self, rule: pd.Series) -> List[Dict[str, Any]]:
        """Execute a threshold/cross-table rule across all ULBs"""
        findings = []
        
        for mp_id in self.data_loader.get_all_ulb_ids():
            finding = self._execute_single_rule(mp_id, rule)
            if finding:
                findings.append(finding)
        
        return findings
    
    def _execute_single_rule(self, mp_id: str, rule: pd.Series) -> Optional[Dict[str, Any]]:
        """Execute a single rule for a single ULB (threshold/cross-table)"""
        primary_table = rule.get('primary_table')
        if pd.isna(primary_table):
            return None
        
        # Extract table name
        if str(primary_table).startswith('mp_'):
            parts = str(primary_table).split('_')
            if len(parts) > 2:
                primary_table = '_'.join(parts[2:])
        
        ulb_data = self.data_loader.get_ulb_data(mp_id, primary_table)
        if ulb_data is None or ulb_data.empty:
            return None
        
        validation_type = str(rule['validation_type']).lower().strip()
        
        if validation_type == 'threshold':
            return self._check_threshold_rule(mp_id, rule, ulb_data)
        elif validation_type == 'consistency':
            return self._check_consistency_rule(mp_id, rule, ulb_data)
        elif validation_type == 'completeness':
            return self._check_completeness_rule(mp_id, rule, ulb_data)
        elif validation_type == 'cross_table':
            return self._check_cross_table_rule(mp_id, rule, ulb_data)
        elif validation_type == 'percentage':
            return self._check_threshold_rule(mp_id, rule, ulb_data)
        return None
    
    def _check_threshold_rule(self, mp_id: str, rule: pd.Series, ulb_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        calc_type = rule.get('calculation_type')
        
        if pd.notna(calc_type) and str(calc_type).lower().strip() != 'none':
            value, error_msg = self.calc_engine.calculate(calc_type, rule, ulb_data)
            value_source = f"{calc_type} calculation"
            if error_msg and self._is_multi_part_rule(rule):
                retry_value, retry_error = self._calculate_with_reference_data(mp_id, rule, ulb_data)
                if retry_error is None:
                    value, error_msg = retry_value, None
                    value_source = f"{calc_type} calculation (multi-part)"
                else:
                    error_msg = retry_error
            if error_msg:
                if "denominator cannot be zero" in error_msg.lower() or "base value cannot be zero" in error_msg.lower():
                    # Not applicable case (e.g., denominator population/staff is zero)
                    return None
                if "non-numeric" in error_msg.lower() or "text/categorical" in error_msg.lower():
                    error_key = f"{rule['checkpoint_id']}:non_numeric"
                    self._log_unique_error(error_key, f"Rule {rule['checkpoint_id']} skipped (non-numeric data in {rule['column_1']})")
                    return None
                return self._create_error_finding(mp_id, rule, error_msg)
        else:
            value, error_msg = self.calc_engine._get_column_value(rule['column_1'], ulb_data)
            value_source = f"column {rule['column_1']}"
            if error_msg:
                if "non-numeric" in error_msg.lower() or "text/categorical" in error_msg.lower():
                    error_key = f"{rule['checkpoint_id']}:non_numeric"
                    self._log_unique_error(error_key, f"Rule {rule['checkpoint_id']} skipped (non-numeric data in {rule['column_1']})")
                    return None
                return self._create_error_finding(mp_id, rule, error_msg)
        
        threshold_spec = rule.get('threshold')
        if pd.isna(threshold_spec):
            return None

        value = self._normalize_year_value(rule, value)
        
        passed, detail = self.threshold_checker.check_threshold(value, threshold_spec, rule)
        if not passed:
            return self._create_finding(mp_id, rule, f"{value_source}: {detail}", value)
        return None

    def _normalize_year_value(self, rule: pd.Series, value: Optional[float]) -> Optional[float]:
        """Normalize Excel serial dates into year when rule is year-like."""
        if value is None:
            return None

        col1 = str(rule.get('column_1', '')).lower()
        desc = str(rule.get('description', '')).lower()
        if ('year' in col1 or 'year' in desc) and 30000 <= value <= 60000:
            excel_epoch = pd.Timestamp('1899-12-30')
            return float((excel_epoch + pd.to_timedelta(value, unit='D')).year)
        return value

    def _is_multi_part_rule(self, rule: pd.Series) -> bool:
        return str(rule.get('multi_part', '')).strip().lower() == 'yes'

    def _calculate_with_reference_data(self, mp_id: str, rule: pd.Series, ulb_data: pd.DataFrame) -> tuple[Optional[float], Optional[str]]:
        """Retry calculations for multi-part rules using reference_table data."""
        ref_table = rule.get('reference_table')
        if pd.isna(ref_table):
            return None, "Reference table is missing"

        if str(ref_table).startswith('mp_'):
            parts = str(ref_table).split('_')
            if len(parts) > 2:
                ref_table = '_'.join(parts[2:])

        ref_data = self.data_loader.get_ulb_data(mp_id, ref_table)
        if ref_data is None or ref_data.empty:
            return None, "Reference table data not found"

        calc_type = str(rule.get('calculation_type', '')).strip().lower()
        val1, err1 = self.calc_engine._get_column_value(rule['column_1'], ulb_data)
        if err1:
            return None, f"Numerator: {err1}"

        val2, err2 = self.calc_engine._get_column_value(rule['column_2'], ref_data)
        if err2:
            return None, f"Denominator: {err2}"

        if calc_type == 'ratio':
            if val2 == 0:
                return None, "Denominator cannot be zero"
            return val1 / val2, None
        if calc_type in ['percentage', 'percentage_of']:
            if val2 == 0:
                return None, "Base value cannot be zero"
            return (val1 / val2) * 100, None
        if calc_type == 'difference':
            return val1 - val2, None

        return None, f"Unsupported multi-part calculation type: {calc_type}"
    
    def _check_consistency_rule(self, mp_id: str, rule: pd.Series, ulb_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        calc_type = str(rule.get('calculation_type', '')).strip().lower()

        if calc_type == 'difference' and pd.notna(rule.get('column_3')):
            expected_val, err1 = self.calc_engine._get_column_value(rule['column_1'], ulb_data)
            if err1:
                if "non-numeric" in err1.lower():
                    return None
                return self._create_error_finding(mp_id, rule, f"Column 1: {err1}")

            minuend, err2 = self.calc_engine._get_column_value(rule['column_2'], ulb_data)
            if err2:
                if "non-numeric" in err2.lower():
                    return None
                return self._create_error_finding(mp_id, rule, f"Column 2: {err2}")

            subtrahend, err3 = self.calc_engine._get_column_value(rule['column_3'], ulb_data)
            if err3:
                if "non-numeric" in err3.lower():
                    return None
                return self._create_error_finding(mp_id, rule, f"Column 3: {err3}")

            val1 = expected_val
            val2 = minuend - subtrahend
        else:
            val1, err1 = self.calc_engine._get_column_value(rule['column_1'], ulb_data)
            if err1:
                if "non-numeric" in err1.lower():
                    return None
                return self._create_error_finding(mp_id, rule, f"Column 1: {err1}")

            val2, err2 = self.calc_engine._get_column_value(rule['column_2'], ulb_data)
            if err2:
                if "non-numeric" in err2.lower():
                    return None
                return self._create_error_finding(mp_id, rule, f"Column 2: {err2}")
        
        operator = str(rule.get('operator', '=')).strip()
        try:
            failed = False
            if operator in ['=', '==']:
                tolerance = max(abs(val2) * 0.01, 0.01)
                failed = abs(val1 - val2) > tolerance
                detail = f"{val1:.2f} != {val2:.2f}"
            elif operator == '>=':
                failed = not (val1 >= val2)
                detail = f"{val1:.2f} not >= {val2:.2f}"
            elif operator == '<=':
                failed = not (val1 <= val2)
                detail = f"{val1:.2f} not <= {val2:.2f}"
            elif operator == '>':
                failed = not (val1 > val2)
                detail = f"{val1:.2f} not > {val2:.2f}"
            elif operator == '<':
                failed = not (val1 < val2)
                detail = f"{val1:.2f} not < {val2:.2f}"
            
            if failed:
                return self._create_finding(mp_id, rule, f"Consistency: {detail}")
        except Exception as e:
            return self._create_error_finding(mp_id, rule, f"Consistency error: {str(e)}")
        return None
    
    def _check_completeness_rule(self, mp_id: str, rule: pd.Series, ulb_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        col_spec = rule['column_1']
        if pd.isna(col_spec):
            return None
        
        col_spec = str(col_spec).strip()
        cols = [c.strip() for c in col_spec.split(',')] if ',' in col_spec else [col_spec]
        
        missing_cols = []
        for col in cols:
            if col not in ulb_data.columns:
                missing_cols.append(col)
            else:
                col_values = ulb_data[col]
                if col_values.isna().all() or (col_values == 0).all():
                    missing_cols.append(col)
        
        if missing_cols:
            return self._create_finding(mp_id, rule, f"Missing/zero: {', '.join(missing_cols)}")
        return None
    
    def _check_cross_table_rule(self, mp_id: str, rule: pd.Series, ulb_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        ref_table = rule.get('reference_table')
        if pd.isna(ref_table):
            return None
        
        if str(ref_table).startswith('mp_'):
            parts = str(ref_table).split('_')
            if len(parts) > 2:
                ref_table = '_'.join(parts[2:])
        
        ref_data = self.data_loader.get_ulb_data(mp_id, ref_table)
        if ref_data is None or ref_data.empty:
            return None
        
        val1, err1 = self.calc_engine._get_column_value(rule['column_1'], ulb_data)
        if err1:
            if "non-numeric" in err1.lower():
                return None
            return self._create_error_finding(mp_id, rule, f"Primary: {err1}")
        
        val2, err2 = self.calc_engine._get_column_value(rule['column_2'], ref_data)
        if err2:
            if "non-numeric" in err2.lower():
                return None
            return self._create_error_finding(mp_id, rule, f"Reference: {err2}")
        
        operator = str(rule.get('operator', '=')).strip()
        try:
            failed = False
            if operator in ['=', '==']:
                tolerance = max(abs(val2) * 0.01, 0.01)
                failed = abs(val1 - val2) > tolerance
                detail = f"{val1:.2f} != {val2:.2f}"
            elif operator == '>=':
                failed = not (val1 >= val2)
                detail = f"{val1:.2f} not >= {val2:.2f}"
            elif operator == '<=':
                failed = not (val1 <= val2)
                detail = f"{val1:.2f} not <= {val2:.2f}"
            elif operator == '>':
                failed = not (val1 > val2)
                detail = f"{val1:.2f} not > {val2:.2f}"
            elif operator == '<':
                failed = not (val1 < val2)
                detail = f"{val1:.2f} not < {val2:.2f}"
            
            if failed:
                detail_text = (
                    f"Cross-table mismatch: primary column '{rule['column_1']}' = {val1:.2f}, "
                    f"reference column '{rule['column_2']}' = {val2:.2f}"
                )
                return self._create_finding(mp_id, rule, detail_text)
        except Exception as e:
            return self._create_error_finding(mp_id, rule, f"Cross-table error: {str(e)}")
        return None
    
    def _create_finding(self, mp_id: str, rule: pd.Series, detail: str, value: Optional[float] = None) -> Dict[str, Any]:
        ulb_info = self.data_loader.get_ulb_info(mp_id)
        severity = str(rule['severity']).capitalize() if pd.notna(rule.get('severity')) else 'Medium'
        
        return {
            'mp_id': mp_id,
            'ulb_name': ulb_info['municipality_name'] if ulb_info else f'ID{mp_id}',
            'district': ulb_info['district_name'] if ulb_info else '',
            'rule_id': rule['checkpoint_id'],
            'part_no': str(rule.get('part', '')),
            'severity': severity,
            'check_type': rule['validation_type'],
            'description': rule['description'],
            'detail': detail,
            'column_1': rule.get('column_1'),
            'column_2': rule.get('column_2'),
            'primary_table': rule.get('primary_table'),
            'reference_table': rule.get('reference_table'),
            'operator': rule.get('operator'),
            'threshold': rule.get('threshold')
        }
    
    def _create_error_finding(self, mp_id: str, rule: pd.Series, error_msg: str) -> Dict[str, Any]:
        ulb_info = self.data_loader.get_ulb_info(mp_id)
        return {
            'mp_id': mp_id,
            'ulb_name': ulb_info['municipality_name'] if ulb_info else f'ID{mp_id}',
            'district': ulb_info['district_name'] if ulb_info else '',
            'rule_id': rule['checkpoint_id'],
            'part_no': str(rule.get('part', '')),
            'severity': 'Medium',
            'check_type': rule['validation_type'],
            'description': rule['description'],
            'detail': f"Unable to evaluate: {error_msg}",
            'column_1': rule.get('column_1'),
            'column_2': rule.get('column_2'),
            'primary_table': rule.get('primary_table'),
            'reference_table': rule.get('reference_table'),
            'operator': rule.get('operator'),
            'threshold': rule.get('threshold')
        }
