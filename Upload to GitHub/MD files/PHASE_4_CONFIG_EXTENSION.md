# Phase 4 Configuration Extension Design
## ULB Audit Validation System - Statistical Rules Support

---

## 📋 Overview

This document defines the extended configuration schema to support:
- **Statistical outlier detection** (IQR, Z-score methods)
- **Inter-ULB peer comparison** (population-based, district-based, type-based)
- **Distribution-based anomaly checks**

**Backward Compatibility**: All existing threshold and cross_table rules remain unchanged.

---

## 🔧 Extended Schema Design

### Current Schema (20 columns)
```
checkpoint_id, part, description, validation_type, calculation_type, 
column_1, column_2, column_3, column_4, operator, threshold, time_period, 
multi_part, reference_part, reference_table, inter_ulb, primary_table, 
enabled, severity, notes
```

### New Columns Added (7 additional columns)

| Column Name | Type | Purpose | Valid Values | Default |
|------------|------|---------|--------------|---------|
| `peer_group_by` | Text | How to group ULBs for comparison | `population_size`, `ulb_type`, `district`, `none`, `null` | `null` |
| `peer_population_min` | Integer | Min population for peer group | e.g., `50000` | `null` |
| `peer_population_max` | Integer | Max population for peer group | e.g., `100000` | `null` |
| `outlier_method` | Text | Statistical method to use | `iqr`, `zscore`, `null` | `null` |
| `iqr_multiplier` | Float | IQR fence multiplier | e.g., `1.5`, `2.0`, `3.0` | `1.5` |
| `stddev_limit` | Float | Z-score threshold | e.g., `2.0`, `2.5`, `3.0` | `2.0` |
| `statistical_context` | Text | Additional notes for statistical rules | Free text | `null` |

### Extended Schema (27 columns total)
```
[Existing 20 columns] + [7 new columns]
```

---

## 📊 New Validation Types

### 1. `outlier_iqr` - Interquartile Range Outlier Detection
Flags values outside Q1 - (IQR × multiplier) or Q3 + (IQR × multiplier)

**Use Case**: Detect extreme values in metrics like revenue per capita, tax collection rates

**Formula**:
```
Q1 = 25th percentile
Q3 = 75th percentile
IQR = Q3 - Q1
Lower Bound = Q1 - (iqr_multiplier × IQR)
Upper Bound = Q3 + (iqr_multiplier × IQR)
Flag if: value < Lower Bound OR value > Upper Bound
```

### 2. `outlier_zscore` - Standard Deviation Outlier Detection
Flags values beyond N standard deviations from mean

**Use Case**: Identify statistical anomalies in normally distributed metrics

**Formula**:
```
Mean = average of all ULB values
StdDev = standard deviation
Z-score = (value - Mean) / StdDev
Flag if: |Z-score| > stddev_limit
```

---

## 🏙️ Peer Grouping Logic

### Grouping Options

#### 1. **`population_size`** - Population-based peers
Compare ULBs within same population bracket
- Requires: `peer_population_min`, `peer_population_max`
- Example: Compare 50K-100K population ULBs together

#### 2. **`ulb_type`** - Type-based peers
Compare municipalities vs corporations separately
- Extracts from ULB name or classification field
- Example: Municipal Corporations compared only with other corporations

#### 3. **`district`** - District-based peers
Compare ULBs within same district
- Uses `district_name` from Part 1 data
- Example: Compare all ULBs in Chennai district

#### 4. **`none`** - Statewide comparison
Compare against entire state dataset
- No grouping applied
- Default for broad metrics

---

## 🎯 Rule Configuration Examples

### Example 1: Revenue Per Capita Outlier (IQR Method)
```
checkpoint_id: STAT-01
part: 3
description: Revenue per capita outlier detection
validation_type: outlier_iqr
calculation_type: ratio
column_1: total_revenue
column_2: total_population
operator: [not used for statistical]
threshold: [not used for statistical]
inter_ulb: Yes (Statistical)
peer_group_by: population_size
peer_population_min: 50000
peer_population_max: 200000
outlier_method: iqr
iqr_multiplier: 1.5
stddev_limit: [null]
statistical_context: Flags ULBs with unusually high/low revenue per capita
```

### Example 2: Property Tax Collection Rate (Z-Score Method)
```
checkpoint_id: STAT-02
part: 4
description: Property tax collection rate anomaly
validation_type: outlier_zscore
calculation_type: percentage
column_1: tax_collected
column_2: tax_demand
operator: [not used]
threshold: [not used]
inter_ulb: Yes (Statistical)
peer_group_by: ulb_type
outlier_method: zscore
stddev_limit: 2.5
iqr_multiplier: [null]
statistical_context: Identifies statistically unusual collection efficiency
```

---

## ✅ Backward Compatibility Rules

1. **All new columns are NULLABLE** - existing rules work without modification
2. **Validation type check**: Statistical processing only triggers when:
   - `validation_type` IN (`outlier_iqr`, `outlier_zscore`)
3. **Engine logic separation**: Statistical rules use different processing pipeline
4. **Existing rule types unaffected**: `threshold`, `cross_table`, `percentage` continue as-is

---

## 🔄 Processing Flow Differences

### Current Flow (Threshold Rules)
```
For each ULB:
  Load ULB data → Apply rule → Check threshold → Generate finding
```

### New Flow (Statistical Rules)
```
Phase 1: Metric Collection
  For each ULB:
    Calculate metric → Store in dataset

Phase 2: Statistical Analysis
  For each peer group:
    Compute Q1, Q3, IQR (or Mean, StdDev)
    Determine bounds

Phase 3: Evaluation
  For each ULB:
    Compare metric to bounds → Generate finding if outside
```

---

## 📝 Validation Rules

### Config Validation Checks
1. If `validation_type` is `outlier_iqr`:
   - `outlier_method` must be 'iqr'
   - `iqr_multiplier` must be provided (default 1.5)
   - `calculation_type` must be valid (ratio, percentage, sum, none)

2. If `validation_type` is `outlier_zscore`:
   - `outlier_method` must be 'zscore'
   - `stddev_limit` must be provided (default 2.0)

3. If `peer_group_by` is 'population_size':
   - `peer_population_min` and `peer_population_max` required

4. Statistical rules must have `inter_ulb` = "Yes (Statistical)"

---

## 🚨 Error Handling

### Insufficient Data
- If peer group has < 10 ULBs: Skip rule, log warning
- If metric cannot be calculated for >50% of ULBs: Skip rule

### Missing Peer Group Fields
- If population data missing: Fall back to statewide comparison
- If district data missing: Use statewide comparison

---

## 📦 Deliverables

1. **Extended Excel Template**: `ValidationRules_v2_Statistical.xlsx`
2. **5 Pilot Statistical Rules** (see next section)
3. **Schema Documentation** (this document)
4. **Migration Guide** (for existing rules)

---

## 🧪 Next Steps

After config finalization:
1. Update `rule_executor.py` with statistical processing layer
2. Add peer grouping logic
3. Enhance finding reports with statistical context
4. Test with pilot rules

---

**Document Version**: 1.0  
**Date**: February 6, 2026  
**Status**: Design Review
