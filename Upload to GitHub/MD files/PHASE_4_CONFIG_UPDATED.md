# Phase 4 Configuration - Updated with Municipality Grade Grouping
## ULB Audit Validation System

**Update Date**: February 6, 2026  
**Change**: Added `municipality_grade` as peer grouping option

---

## 🆕 Updated Peer Grouping Options

### Complete List of peer_group_by Values

| Value | Description | Additional Fields Required | Use Case |
|-------|-------------|---------------------------|----------|
| `population_size` | Group by population brackets | `peer_population_min`, `peer_population_max` | Compare similar-sized ULBs |
| `district` | Group by district | None (auto-detected) | Regional comparison |
| `municipality_grade` | **NEW** - Group by grade classification | None (auto-detected from Part 1) | Compare ULBs of same grade |
| `none` | Statewide comparison | None | Absolute benchmarking |

---

## 🏛️ Municipality Grade Grouping (NEW)

### What is Municipality Grade?

Tamil Nadu municipalities are classified into different grades based on:
- Population size
- Revenue generation capacity
- Administrative classification
- Service delivery standards

Common grades include:
- **Selection Grade** (largest, most developed)
- **Special Grade**
- **Grade I**
- **Grade II**
- **Grade III** (smallest)
- **Municipal Corporations** (separate category)

### Why Use Grade-Based Grouping?

Municipalities within the same grade have:
- Similar administrative structures
- Comparable resource levels
- Similar service delivery expectations
- Aligned governance standards

**Better than population alone**: Two municipalities with similar populations but different grades may have different capacities and expectations.

### Configuration Example

```excel
checkpoint_id:        STAT-06
part:                 3
description:          Revenue efficiency by municipality grade
validation_type:      outlier_iqr
calculation_type:     ratio
column_1:             p3_2_3_revenue
column_2:             p1_1_3_4_tot_25_no
inter_ulb:            Yes (Statistical)
primary_table:        mp_270126_p3
enabled:              True
severity:             high
peer_group_by:        municipality_grade   ← NEW VALUE
peer_population_min:  [blank]
peer_population_max:  [blank]
outlier_method:       iqr
iqr_multiplier:       1.5
statistical_context:  Compares revenue per capita within same municipality grade
```

---

## 📊 Complete Peer Grouping Decision Matrix

### When to Use Each Option

| Scenario | Best peer_group_by | Rationale |
|----------|-------------------|-----------|
| Infrastructure coverage varies by population | `population_size` | Service norms differ by size |
| Regional economic conditions matter | `district` | Local context important |
| Administrative capacity affects performance | `municipality_grade` | Grade determines resources |
| Policy should apply uniformly | `none` | Statewide standard |
| Financial metrics (revenue, expenditure) | `municipality_grade` | Grade-based budgeting |
| Service levels (water, roads) | `population_size` or `municipality_grade` | Depends on norms |
| Tax collection efficiency | `district` or `municipality_grade` | Regional or capacity-based |
| Staffing ratios | `municipality_grade` | Organizational structure |

---

## 🔍 Data Source for Grouping

### Population Size
**Source**: `p1_1_3_4_tot_25_no` from Part 1  
**Logic**: Filter ULBs where population between min and max

### District
**Source**: `district_name` from Part 1  
**Logic**: Group all ULBs in same district

### Municipality Grade (NEW)
**Source**: Extracted from `municipality_name` or `ulb_type` field in Part 1  
**Logic**: Parse grade from name (e.g., "Ariyalur Municipality - Grade I")  
**Fallback**: If not in name, use classification logic based on population + revenue

---

## 💡 Example Statistical Rules Using All Groupings

### Rule 1: Population-Based (Infrastructure)
```
Water supply coverage outlier among similar-sized ULBs
peer_group_by: population_size
peer_population_min: 100000
peer_population_max: 500000
Rationale: Infrastructure needs scale with population
```

### Rule 2: District-Based (Regional)
```
Property tax collection rate within district
peer_group_by: district
Rationale: Local economic conditions affect collection
```

### Rule 3: Grade-Based (Administrative) - NEW
```
Staff per capita outlier by municipality grade
peer_group_by: municipality_grade
Rationale: Staffing norms tied to grade classification
```

### Rule 4: Statewide (Universal)
```
Revenue per capita statewide outlier
peer_group_by: none
Rationale: Financial health should meet minimum statewide standard
```

---

## 🔄 Updated Schema Summary

### peer_group_by Column
**Data Type**: Text  
**Allowed Values**: `population_size`, `district`, `municipality_grade`, `none`, `null`  
**Default**: `null` (for non-statistical rules)  
**Nullable**: Yes

### No New Columns Required
✅ All existing 27 columns sufficient  
✅ `municipality_grade` uses existing schema  
✅ Backward compatible with all existing rules

---

## 🧪 Pilot Rule Example with Municipality Grade

```excel
checkpoint_id:        STAT-06
part:                 2
description:          Administrative staff ratio by municipality grade
validation_type:      outlier_zscore
calculation_type:     ratio
column_1:             p2_2_1_admin_staff
column_2:             p1_1_3_4_tot_25_no
multi_part:           Yes
reference_part:       1
reference_table:      mp_270126_p1_1_1_2
inter_ulb:            Yes (Statistical)
primary_table:        mp_270126_p2_2_1_1_2_1_5
enabled:              True
severity:             medium
notes:                Phase 4. Grade-based staff comparison.
peer_group_by:        municipality_grade
peer_population_min:  [blank]
peer_population_max:  [blank]
outlier_method:       zscore
iqr_multiplier:       [blank]
stddev_limit:         2.0
statistical_context:  Flags ULBs with unusual admin staffing levels compared to 
                      municipalities of same grade classification.
```

---

## 🛠️ Engine Implementation Requirements

### Grade Extraction Logic
```python
def extract_municipality_grade(ulb_name):
    """Extract grade from municipality name"""
    grade_patterns = [
        r'Grade\s+([IVX]+)',           # "Grade I", "Grade II"
        r'(\w+)\s+Grade',               # "Selection Grade", "Special Grade"
        r'Municipal\s+Corporation',     # Corporations separate
    ]
    # Parse and return grade
    # Fallback: classify by population + revenue thresholds
```

### Peer Grouping Function Update
```python
def group_ulbs_by_peer_criteria(self, rule):
    if rule['peer_group_by'] == 'population_size':
        return self.group_by_population(rule)
    elif rule['peer_group_by'] == 'district':
        return self.group_by_district()
    elif rule['peer_group_by'] == 'municipality_grade':  # NEW
        return self.group_by_municipality_grade()
    else:  # 'none'
        return {'statewide': self.data_loader.get_all_ulb_ids()}
```

---

## ✅ Updated Validation Rules

### Configuration Validation
```
IF peer_group_by = 'municipality_grade':
  ✓ peer_population_min should be blank
  ✓ peer_population_max should be blank
  ✓ Engine will auto-extract grade from Part 1 data
  ✓ Minimum 3 ULBs per grade required for statistics
```

---

## 📈 Expected Peer Groups

Based on Tamil Nadu municipal structure:

| Grade Category | Typical Count | Example Metrics |
|---------------|---------------|-----------------|
| Municipal Corporations | 15-20 | High revenue, large staff |
| Selection Grade | 10-15 | Above-average capacity |
| Special Grade | 20-30 | Medium capacity |
| Grade I | 40-60 | Standard capacity |
| Grade II | 50-80 | Basic capacity |
| Grade III | 30-50 | Smallest municipalities |

---

## 🎯 Summary of Changes

### What's New
✅ Added `municipality_grade` as 4th peer grouping option  
✅ No new columns required (uses existing schema)  
✅ Documentation updated with examples  
✅ Engine implementation guidelines provided

### What's Unchanged
✅ All 27 existing columns remain the same  
✅ All 76 existing rules unaffected  
✅ Backward compatibility maintained  
✅ Configuration structure unchanged

### Next Steps
1. ✅ Documentation updated (this document)
2. 🔜 Implement grade extraction in engine
3. 🔜 Add grade-based grouping logic
4. 🔜 Test with pilot rule using municipality_grade

---

**Document Version**: 1.1  
**Status**: Ready for Engine Implementation  
**Configuration File**: ValidationRules_v2_Statistical_Extended.xlsx (no changes needed)
