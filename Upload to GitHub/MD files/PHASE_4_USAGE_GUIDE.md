# Phase 4 Statistical Rules - Configuration Guide
## ULB Audit Validation System

---

## 📚 Quick Reference

### New Validation Types
- **`outlier_iqr`** - Interquartile Range method for detecting extreme values
- **`outlier_zscore`** - Standard deviation method for anomaly detection

### New Configuration Columns (7 total)
```
peer_group_by, peer_population_min, peer_population_max, 
outlier_method, iqr_multiplier, stddev_limit, statistical_context
```

---

## 🎯 How to Create Statistical Rules

### Template 1: IQR Outlier Detection

```excel
checkpoint_id:        STAT-XX
part:                 [1-9]
description:          [Clear description of what you're checking]
validation_type:      outlier_iqr
calculation_type:     ratio | percentage | sum | none
column_1:             [numerator column]
column_2:             [denominator column] (or blank if calculation_type = none)
column_3:             [blank]
column_4:             [blank]
operator:             [blank - not used for statistical]
threshold:            [blank - not used for statistical]
time_period:          [blank or specific period]
multi_part:           Yes | No
reference_part:       [if multi_part = Yes]
reference_table:      [if multi_part = Yes]
inter_ulb:            Yes (Statistical)
primary_table:        mp_270126_pX
enabled:              True
severity:             critical | high | medium | low
notes:                [Description and phase]

# NEW COLUMNS FOR STATISTICAL RULES
peer_group_by:        population_size | district | none
peer_population_min:  [if peer_group_by = population_size]
peer_population_max:  [if peer_group_by = population_size]
outlier_method:       iqr
iqr_multiplier:       1.5 | 2.0 | 3.0
stddev_limit:         [blank]
statistical_context:  [Explanation of what finding means]
```

### Template 2: Z-Score Outlier Detection

```excel
checkpoint_id:        STAT-XX
part:                 [1-9]
description:          [Clear description]
validation_type:      outlier_zscore
calculation_type:     ratio | percentage | sum | none
column_1:             [primary metric column]
column_2:             [denominator if ratio/percentage]
operator:             [blank]
threshold:            [blank]
inter_ulb:            Yes (Statistical)
primary_table:        mp_270126_pX
enabled:              True
severity:             critical | high | medium | low

# NEW COLUMNS
peer_group_by:        population_size | district | none
peer_population_min:  [if applicable]
peer_population_max:  [if applicable]
outlier_method:       zscore
iqr_multiplier:       [blank]
stddev_limit:         2.0 | 2.5 | 3.0
statistical_context:  [Context for findings]
```

---

## 🧮 Calculation Type Examples

### 1. **`ratio`** - Division
```
Metric = column_1 / column_2
Example: Population per sq km = total_population / area
Example: Revenue per capita = total_revenue / population
```

### 2. **`percentage`** - Ratio × 100
```
Metric = (column_1 / column_2) × 100
Example: Collection efficiency = (tax_collected / tax_demand) × 100
Example: Water coverage = (households_covered / total_households) × 100
```

### 3. **`sum`** - Addition
```
Metric = column_1 + column_2 + column_3 + column_4
Example: Total expenditure = salaries + maintenance + capital + other
```

### 4. **`none`** - Direct value
```
Metric = column_1 (no calculation)
Example: Check area values directly
Example: Check raw population numbers
```

---

## 🏙️ Peer Grouping Options

### Option 1: Population Size Brackets
```
peer_group_by: population_size
peer_population_min: 50000
peer_population_max: 200000
```
**Effect**: Compare only ULBs with population between 50K-200K

**Use When**:
- Population size significantly affects the metric
- Small towns vs large cities have different norms
- Example: Staffing ratios, infrastructure coverage

### Option 2: District-Level Comparison
```
peer_group_by: district
peer_population_min: [blank]
peer_population_max: [blank]
```
**Effect**: Compare ULBs within same district

**Use When**:
- Regional factors matter (geography, economy, policies)
- Local context important
- Example: Tax collection rates, service levels

### Option 3: Statewide Comparison
```
peer_group_by: none
peer_population_min: [blank]
peer_population_max: [blank]
```
**Effect**: Compare against entire state dataset

**Use When**:
- Metric should be consistent across all ULBs
- Absolute performance matters
- Example: Financial compliance, basic service coverage

### Option 4: ULB Type (Future)
```
peer_group_by: ulb_type
```
**Effect**: Compare municipalities vs corporations separately
**Status**: Reserved for future implementation

---

## 📊 Statistical Method Selection

### When to Use IQR Method
```
outlier_method: iqr
iqr_multiplier: 1.5 (standard) | 2.0 (moderate) | 3.0 (conservative)
```

**Best For**:
- Skewed distributions
- Metrics with natural extreme values
- When you want to flag "unusual but not impossible"

**Sensitivity**:
- 1.5 → More sensitive (flags ~5% of data as outliers)
- 2.0 → Moderate (flags ~2-3%)
- 3.0 → Conservative (flags only extreme outliers)

**Examples**:
- Revenue per capita (high earners skew distribution)
- Population density (varies naturally)
- Tax collection rates

### When to Use Z-Score Method
```
outlier_method: zscore
stddev_limit: 2.0 (standard) | 2.5 (moderate) | 3.0 (conservative)
```

**Best For**:
- Normally distributed data
- Symmetric distributions
- When you want statistical precision

**Sensitivity**:
- 2.0 → ~5% flagged (95% confidence)
- 2.5 → ~1% flagged (99% confidence)
- 3.0 → ~0.3% flagged (99.7% confidence)

**Examples**:
- Staffing levels (tend to cluster around mean)
- Service coverage percentages
- Administrative ratios

---

## ✅ Configuration Validation Rules

### Rule 1: Validation Type Consistency
```
IF validation_type = 'outlier_iqr':
  ✓ outlier_method MUST be 'iqr'
  ✓ iqr_multiplier MUST be provided (default: 1.5)
  ✗ stddev_limit should be blank

IF validation_type = 'outlier_zscore':
  ✓ outlier_method MUST be 'zscore'
  ✓ stddev_limit MUST be provided (default: 2.0)
  ✗ iqr_multiplier should be blank
```

### Rule 2: Peer Grouping Consistency
```
IF peer_group_by = 'population_size':
  ✓ peer_population_min REQUIRED
  ✓ peer_population_max REQUIRED
  ✓ peer_population_max > peer_population_min

IF peer_group_by = 'district':
  ✗ peer_population_min and _max should be blank

IF peer_group_by = 'none':
  ✗ peer_population_min and _max should be blank
```

### Rule 3: Multi-Part References
```
IF multi_part = 'Yes':
  ✓ reference_part REQUIRED
  ✓ reference_table REQUIRED
  
Example:
  To use population from Part 1 in Part 3 rule:
  multi_part: Yes
  reference_part: 1
  reference_table: mp_270126_p1_1_1_2
```

### Rule 4: Inter-ULB Flag
```
All statistical rules MUST have:
  inter_ulb: "Yes (Statistical)"
```

---

## 🎓 Complete Examples

### Example 1: Population Density (Population-Based Peers)
```excel
checkpoint_id:        STAT-01
part:                 1
description:          Population density outlier detection (persons per sq km)
validation_type:      outlier_iqr
calculation_type:     ratio
column_1:             p1_1_3_4_tot_25_no
column_2:             p1_1_1_3_area
inter_ulb:            Yes (Statistical)
primary_table:        mp_270126_p1_1_1_2
enabled:              True
severity:             medium
peer_group_by:        population_size
peer_population_min:  50000
peer_population_max:  200000
outlier_method:       iqr
iqr_multiplier:       1.5
statistical_context:  Flags ULBs with unusually high or low population density 
                      compared to peers in same size bracket.
```

### Example 2: Revenue Per Capita (Statewide)
```excel
checkpoint_id:        STAT-02
part:                 3
description:          Revenue per capita outlier (statewide comparison)
validation_type:      outlier_zscore
calculation_type:     ratio
column_1:             p3_2_3_revenue
column_2:             p1_1_3_4_tot_25_no
multi_part:           Yes
reference_part:       1
reference_table:      mp_270126_p1_1_1_2
inter_ulb:            Yes (Statistical)
primary_table:        mp_270126_p3
enabled:              True
severity:             high
peer_group_by:        none
outlier_method:       zscore
stddev_limit:         2.5
statistical_context:  Identifies ULBs with statistically unusual revenue 
                      generation capability (>2.5 std dev from mean).
```

### Example 3: Tax Collection (District Peers)
```excel
checkpoint_id:        STAT-03
part:                 4
description:          Property tax collection efficiency outlier (district peers)
validation_type:      outlier_iqr
calculation_type:     percentage
column_1:             p4_6_1_b_collection
column_2:             p4_6_1_a_demand
inter_ulb:            Yes (Statistical)
primary_table:        mp_270126_p4
enabled:              True
severity:             high
peer_group_by:        district
outlier_method:       iqr
iqr_multiplier:       1.5
statistical_context:  Compares collection efficiency within same district 
                      to identify best/worst performers.
```

---

## 🚨 Common Mistakes to Avoid

### ❌ Mistake 1: Wrong Method Specified
```
validation_type: outlier_iqr
outlier_method: zscore  ← WRONG! Should be 'iqr'
```

### ❌ Mistake 2: Missing Peer Group Bounds
```
peer_group_by: population_size
peer_population_min: [blank]  ← WRONG! Must specify range
peer_population_max: [blank]
```

### ❌ Mistake 3: Using Threshold with Statistical Rules
```
validation_type: outlier_iqr
threshold: 100  ← WRONG! Statistical rules don't use thresholds
operator: >     ← WRONG! Not used
```

### ❌ Mistake 4: Wrong Inter-ULB Value
```
inter_ulb: Yes  ← Should be "Yes (Statistical)" for clarity
```

---

## 📋 Pre-Deployment Checklist

Before adding a new statistical rule:

- [ ] Verified column names exist in data files
- [ ] Chose appropriate calculation_type
- [ ] Selected correct statistical method (IQR vs Z-score)
- [ ] Set appropriate sensitivity (multiplier/limit)
- [ ] Defined peer grouping strategy
- [ ] Wrote clear statistical_context
- [ ] Set appropriate severity level
- [ ] Tested column references (multi_part if needed)
- [ ] Reviewed peer group will have enough ULBs (>10 recommended)

---

## 🔄 Migration from v1 to v2

### For Existing Rules:
✅ **No action needed** - All 71 existing rules work as-is
✅ New columns automatically set to NULL/blank
✅ Processing logic unchanged for threshold/cross_table rules

### To Add Statistical Rules:
1. Open `ValidationRules_v2_Statistical_Extended.xlsx`
2. Use "Statistical_Rules_Only" sheet as reference
3. Copy template row, modify values
4. Ensure validation consistency (see checklist)
5. Test with pilot run before full deployment

---

## 📖 Further Reading

- **PHASE_4_CONFIG_EXTENSION.md** - Technical design document
- **Schema_Documentation** sheet - Complete column definitions
- **Phase_4_Summary** sheet - Extension overview
- **Statistical_Rules_Only** sheet - All statistical rules

---

**Document Version**: 1.0  
**Last Updated**: February 6, 2026  
**Status**: Ready for Engine Implementation
