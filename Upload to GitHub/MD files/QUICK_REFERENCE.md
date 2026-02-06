# Phase 4 Quick Reference Card
## Statistical Validation Rules Configuration

---

## 📋 NEW VALIDATION TYPES

### 🔹 outlier_iqr
**Interquartile Range Method**
```
Flags values outside: Q1 - (k × IQR) or Q3 + (k × IQR)
Best for: Skewed data, natural extremes
Sensitivity: 1.5 (standard), 2.0 (moderate), 3.0 (conservative)
```

### 🔹 outlier_zscore
**Z-Score Method**
```
Flags values beyond: Mean ± (z × StdDev)
Best for: Normal distributions, symmetric data
Sensitivity: 2.0 (95%), 2.5 (99%), 3.0 (99.7%)
```

---

## 🎯 PEER GROUPING OPTIONS

| peer_group_by | Use When | Requires |
|---------------|----------|----------|
| `population_size` | Compare similar-sized ULBs | `peer_population_min`, `peer_population_max` |
| `district` | Regional comparison | Nothing (auto-detected) |
| `none` | Statewide benchmark | Nothing |

---

## 📊 CALCULATION TYPES

| Type | Formula | Example |
|------|---------|---------|
| `ratio` | col1 / col2 | Population per sq km |
| `percentage` | (col1 / col2) × 100 | Collection efficiency % |
| `sum` | col1 + col2 + ... | Total expenditure |
| `none` | col1 | Direct value |

---

## ✅ CONFIGURATION TEMPLATE

### IQR Template
```excel
checkpoint_id:        STAT-XX
validation_type:      outlier_iqr
calculation_type:     ratio | percentage | sum | none
column_1:             [numerator]
column_2:             [denominator]
inter_ulb:            Yes (Statistical)
enabled:              True
severity:             high | medium | low
peer_group_by:        population_size | district | none
peer_population_min:  [if population_size]
peer_population_max:  [if population_size]
outlier_method:       iqr
iqr_multiplier:       1.5 | 2.0 | 3.0
statistical_context:  [Explanation]
```

### Z-Score Template
```excel
checkpoint_id:        STAT-XX
validation_type:      outlier_zscore
calculation_type:     ratio | percentage | sum | none
column_1:             [primary metric]
column_2:             [denominator if ratio]
inter_ulb:            Yes (Statistical)
enabled:              True
severity:             high | medium | low
peer_group_by:        population_size | district | none
outlier_method:       zscore
stddev_limit:         2.0 | 2.5 | 3.0
statistical_context:  [Explanation]
```

---

## 🔥 COMMON MISTAKES

❌ `validation_type: outlier_iqr` + `outlier_method: zscore`  
✅ Methods must match validation types

❌ `peer_group_by: population_size` + no min/max  
✅ Population grouping needs bounds

❌ Using `threshold` or `operator` with statistical rules  
✅ These fields are ignored (leave blank)

❌ `inter_ulb: Yes`  
✅ Use "Yes (Statistical)" for clarity

---

## 📈 SENSITIVITY GUIDE

### IQR Multiplier
- **1.5**: Standard (≈5% flagged) - Use for most cases
- **2.0**: Moderate (≈2-3% flagged) - Less sensitive
- **3.0**: Conservative (only extremes) - Very strict

### Z-Score Limit
- **2.0**: Standard (≈5% flagged) - 95% confidence
- **2.5**: Moderate (≈1% flagged) - 99% confidence
- **3.0**: Conservative (≈0.3% flagged) - 99.7% confidence

---

## 🎓 PILOT RULES SUMMARY

| ID | Description | Method | Grouping | Part |
|----|-------------|--------|----------|------|
| STAT-01 | Population density | IQR (1.5) | Pop 50k-200k | 1 |
| STAT-02 | Revenue per capita | Z (2.5) | Statewide | 3 |
| STAT-03 | Tax collection rate | IQR (1.5) | District | 4 |
| STAT-04 | Water coverage | IQR (2.0) | Pop 100k-500k | 8 |
| STAT-05 | Staff per 1000 pop | Z (2.0) | Statewide | 2 |

---

## 🔄 BACKWARD COMPATIBILITY

✅ All 71 existing rules unchanged  
✅ 7 new columns added (optional)  
✅ Old rules ignore new columns  
✅ Engine processes types separately  

**Version**: v2 (27 columns)  
**Previous**: v1 (20 columns)  

---

## 📚 FULL DOCUMENTATION

- **Design**: PHASE_4_CONFIG_EXTENSION.md
- **Usage**: PHASE_4_USAGE_GUIDE.md
- **Implementation**: PHASE_4_IMPLEMENTATION_SUMMARY.md
- **Excel**: ValidationRules_v2_Statistical_Extended.xlsx

---

**Status**: ✅ Config Complete | 🔜 Engine Pending  
**Date**: February 6, 2026
