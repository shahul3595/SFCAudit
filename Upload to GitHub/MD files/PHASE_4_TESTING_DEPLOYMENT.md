# Phase 4 Testing & Deployment Guide
## Statistical Engine Verification and Production Rollout

**Date**: February 6, 2026  
**Purpose**: Step-by-step guide to test and deploy Phase 4 statistical engine

---

## 🧪 TESTING WORKFLOW

### Pre-Test Checklist
- [ ] Backup current `rule_executor.py`
- [ ] Have `ValidationRules_v2_Statistical_Extended.xlsx` ready
- [ ] Ensure all 24 CSV data files are in `/data` folder
- [ ] Python environment with pandas, numpy installed

---

## 📋 PHASE 1: INSTALLATION

### Step 1: Backup Current System
```bash
cd ulb_audit_system
cp scripts/rule_executor.py scripts/rule_executor_backup.py
cp config/ValidationRules_v1_Corrected.xlsx config/ValidationRules_v1_Corrected_backup.xlsx
```

### Step 2: Install Phase 4 Files
```bash
# Install new engine
cp rule_executor_phase4.py scripts/rule_executor.py

# Install new config
cp ValidationRules_v2_Statistical_Extended.xlsx config/ValidationRules_v1_Corrected.xlsx
```

**Note**: We overwrite the old filename to keep run_audit.py working without changes.

### Step 3: Verify Installation
```bash
# Check Python can import the new module
cd scripts
python -c "from rule_executor import StatisticalEngine; print('✓ StatisticalEngine imported')"
```

Expected output:
```
✓ StatisticalEngine imported
```

---

## 🧪 PHASE 2: UNIT TESTING

### Test 1: Grade Extraction
Create test script `test_grade_extraction.py`:

```python
import pandas as pd
import sys
sys.path.insert(0, 'scripts')
from rule_executor import StatisticalEngine
from data_loader import DataLoader

# Mock data loader
class MockDataLoader:
    def get_all_ulb_ids(self):
        return []

calc_engine = None
stat_engine = StatisticalEngine(MockDataLoader(), calc_engine)

# Test cases
test_cases = [
    ("Ariyalur Municipality - Grade I", "Grade I"),
    ("Coimbatore Selection Grade", "Selection Grade"),
    ("Chennai Municipal Corporation", "Municipal Corporation"),
    ("Dindigul Special Grade Municipality", "Special Grade"),
    ("XYZ Municipality", "Municipality (Unclassified)"),
]

print("Testing Municipality Grade Extraction:")
print("="*60)
for ulb_name, expected in test_cases:
    result = stat_engine.extract_municipality_grade(ulb_name)
    status = "✓" if result == expected else "✗"
    print(f"{status} {ulb_name[:40]:40s} → {result}")

print("="*60)
```

Run:
```bash
python test_grade_extraction.py
```

Expected: All tests pass (✓)

### Test 2: IQR Calculation
Create test script `test_iqr.py`:

```python
import sys
sys.path.insert(0, 'scripts')
from rule_executor import StatisticalEngine

class MockDataLoader:
    def get_all_ulb_ids(self): return []

stat_engine = StatisticalEngine(MockDataLoader(), None)

# Test data: values from 1 to 100
test_values = list(range(1, 101))

bounds = stat_engine.calculate_iqr_bounds(test_values, multiplier=1.5)

print("IQR Calculation Test:")
print("="*60)
print(f"Test Data: 1 to 100 (N=100)")
print(f"Q1 (25th percentile): {bounds['q1']:.2f} (Expected: ~25)")
print(f"Q3 (75th percentile): {bounds['q3']:.2f} (Expected: ~75)")
print(f"IQR: {bounds['iqr']:.2f} (Expected: ~50)")
print(f"Lower Bound: {bounds['lower_bound']:.2f}")
print(f"Upper Bound: {bounds['upper_bound']:.2f}")
print("="*60)

# Verify
assert 24 <= bounds['q1'] <= 26, "Q1 should be ~25"
assert 74 <= bounds['q3'] <= 76, "Q3 should be ~75"
assert 49 <= bounds['iqr'] <= 51, "IQR should be ~50"
print("✓ All assertions passed!")
```

Run:
```bash
python test_iqr.py
```

Expected: All assertions pass

### Test 3: Z-Score Calculation
Create test script `test_zscore.py`:

```python
import sys
sys.path.insert(0, 'scripts')
from rule_executor import StatisticalEngine

class MockDataLoader:
    def get_all_ulb_ids(self): return []

stat_engine = StatisticalEngine(MockDataLoader(), None)

# Test data: normally distributed around mean=50, std≈29
test_values = list(range(1, 101))

bounds = stat_engine.calculate_zscore_bounds(test_values, stddev_limit=2.0)

print("Z-Score Calculation Test:")
print("="*60)
print(f"Test Data: 1 to 100 (N=100)")
print(f"Mean: {bounds['mean']:.2f} (Expected: 50.5)")
print(f"Std Dev: {bounds['std']:.2f} (Expected: ~29)")
print(f"Lower Bound: {bounds['lower_bound']:.2f}")
print(f"Upper Bound: {bounds['upper_bound']:.2f}")
print("="*60)

# Verify
assert 50 <= bounds['mean'] <= 51, "Mean should be ~50.5"
assert 28 <= bounds['std'] <= 30, "Std should be ~29"
print("✓ All assertions passed!")
```

Run:
```bash
python test_zscore.py
```

Expected: All assertions pass

---

## 🔍 PHASE 3: INTEGRATION TESTING

### Test 4: Run with Single Statistical Rule

**Modify config to enable ONLY STAT-01:**

Open `ValidationRules_v2_Statistical_Extended.xlsx`:
1. Set `enabled = False` for all rules EXCEPT STAT-01
2. Save file

**Run audit:**
```bash
cd ulb_audit_system
python scripts/run_audit.py
```

**What to check:**
1. Log shows: `[2/2] Executing 1 statistical rules...`
2. No errors in console
3. Report generated successfully
4. PDF contains statistical findings with:
   - IQR bounds shown
   - Peer group info (pop_50k-200k)
   - Statistical context message

**Expected findings:** 2-5 outliers (out of ~147 ULBs)

### Test 5: Run with All 5 Pilot Rules

**Modify config:**
1. Set `enabled = True` for STAT-01 through STAT-05
2. Set `enabled = True` for all threshold rules
3. Save file

**Run full audit:**
```bash
python scripts/run_audit.py
```

**What to check:**
1. Log shows: `[1/2] Executing N threshold/cross-table rules...`
2. Log shows: `[2/2] Executing 5 statistical rules...`
3. Each statistical rule logs: `✓ Found X statistical outliers`
4. Master dashboard includes statistical findings
5. Individual ULB reports show statistical findings separately

**Expected total findings:** 
- Threshold: ~100-200 (from existing rules)
- Statistical: ~10-25 (from 5 pilot rules)

---

## 📊 PHASE 4: VALIDATION

### Validation 1: Manual Calculation Check

Pick one ULB that appears in STAT-01 findings.

**Manual verification:**
1. Calculate population density = population / area
2. Get all ULB densities in peer group (50k-200k pop)
3. Calculate Q1, Q3, IQR manually
4. Verify bounds: Q1 - 1.5*IQR, Q3 + 1.5*IQR
5. Confirm ULB is indeed outside bounds

**Tool:** Use Excel or Python notebook for manual calculation

**Template:**
```python
import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('data/mp_270126_p1_1_1_2.csv')

# Filter peer group
df_peer = df[
    (df['p1_1_3_4_tot_25_no'] >= 50000) & 
    (df['p1_1_3_4_tot_25_no'] <= 200000)
]

# Calculate density
df_peer['density'] = df_peer['p1_1_3_4_tot_25_no'] / df_peer['p1_1_1_3_area']

# Calculate IQR
q1 = df_peer['density'].quantile(0.25)
q3 = df_peer['density'].quantile(0.75)
iqr = q3 - q1
lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr

print(f"Q1: {q1:.2f}")
print(f"Q3: {q3:.2f}")
print(f"IQR: {iqr:.2f}")
print(f"Lower: {lower:.2f}")
print(f"Upper: {upper:.2f}")

# Find outliers
outliers = df_peer[
    (df_peer['density'] < lower) | (df_peer['density'] > upper)
]

print(f"\nOutliers: {len(outliers)}")
print(outliers[['mp_id', 'municipality_name', 'density']])
```

**Compare with engine output** - should match exactly!

### Validation 2: Peer Group Verification

**Check population grouping:**
```python
# Count ULBs in each population bracket
df = pd.read_csv('data/mp_270126_p1_1_1_2.csv')

# STAT-01 group
group1 = df[(df['p1_1_3_4_tot_25_no'] >= 50000) & 
            (df['p1_1_3_4_tot_25_no'] <= 200000)]
print(f"STAT-01 peer group size: {len(group1)}")

# STAT-04 group
group2 = df[(df['p1_1_3_4_tot_25_no'] >= 100000) & 
            (df['p1_1_3_4_tot_25_no'] <= 500000)]
print(f"STAT-04 peer group size: {len(group2)}")
```

**Verify log output matches:**
```
(peer group: pop_50k-200k, N=XX)
(peer group: pop_100k-500k, N=YY)
```

### Validation 3: Grade Extraction Verification

```python
df = pd.read_csv('data/mp_270126_p1_1_1_2.csv')

import sys
sys.path.insert(0, 'scripts')
from rule_executor import StatisticalEngine

class MockDataLoader:
    def get_all_ulb_ids(self): return []

stat_engine = StatisticalEngine(MockDataLoader(), None)

# Extract grades
df['extracted_grade'] = df['municipality_name'].apply(
    stat_engine.extract_municipality_grade
)

# Count by grade
print(df['extracted_grade'].value_counts())
```

Expected: Meaningful groupings like:
- Municipal Corporation: 15-20
- Selection Grade: 10-15
- Grade I: 40-60
- etc.

---

## ⚠️ PHASE 5: EDGE CASE TESTING

### Edge Case 1: Small Peer Groups
**Test:** Set population range with only 2 ULBs
**Expected:** Engine skips (logs warning "Insufficient data")

### Edge Case 2: Missing Columns
**Test:** Create rule with invalid column name
**Expected:** Engine skips gracefully, logs error

### Edge Case 3: All Null Values
**Test:** Rule using column with all nulls in peer group
**Expected:** Engine skips, no crash

### Edge Case 4: Division by Zero
**Test:** Ratio calculation where denominator is zero
**Expected:** Metric = None for that ULB, excluded from stats

---

## 🚀 PHASE 6: PRODUCTION DEPLOYMENT

### Pre-Deployment Checklist
- [ ] All unit tests passed
- [ ] Integration tests passed
- [ ] Manual calculations verified
- [ ] Edge cases handled gracefully
- [ ] No errors in full audit run
- [ ] Reports generated successfully
- [ ] Statistical findings make sense
- [ ] Threshold rules still work (regression test)

### Deployment Steps

**Step 1: Final Backup**
```bash
# Create backup folder
mkdir -p backups/pre_phase4
cp scripts/rule_executor.py backups/pre_phase4/
cp config/ValidationRules_v1_Corrected.xlsx backups/pre_phase4/
```

**Step 2: Deploy to Production**
```bash
# Copy Phase 4 files
cp rule_executor_phase4.py scripts/rule_executor.py
cp ValidationRules_v2_Statistical_Extended.xlsx config/ValidationRules_v1_Corrected.xlsx
```

**Step 3: Production Test Run**
```bash
# Run complete audit
python scripts/run_audit.py > deployment_test.log 2>&1

# Check for errors
grep -i "error\|exception\|failed" deployment_test.log
```

If no errors → ✅ Deployment successful!

**Step 4: Archive Logs**
```bash
# Save deployment logs
cp logs/audit_log_*.log backups/pre_phase4/
cp deployment_test.log backups/pre_phase4/
```

---

## 📈 PHASE 7: POST-DEPLOYMENT MONITORING

### Week 1: Initial Monitoring

**Daily checks:**
1. Review statistical findings for obvious errors
2. Check audit completion rate (should be 100%)
3. Monitor log file sizes (shouldn't explode)
4. Spot-check 2-3 ULB reports for quality

**Red flags:**
- ❌ Audit fails to complete
- ❌ All ULBs flagged as outliers (bad bounds)
- ❌ No statistical findings at all (rules not running)
- ❌ Crash logs with stack traces

### Month 1: Tuning Phase

**Collect feedback:**
- Are sensitivity levels appropriate?
- Too many/few statistical findings?
- Peer groupings make sense?

**Adjust as needed:**
- IQR multipliers: 1.5 → 2.0 if too sensitive
- Z-score limits: 2.0 → 2.5 if too sensitive
- Population brackets: Adjust if groups too small/large

### Ongoing: Continuous Improvement

**Add new rules based on:**
- Audit team requirements
- Domain expert input
- Patterns discovered in data

**Optimize performance:**
- Cache peer groups if slow
- Parallelize metric collection
- Profile bottlenecks

---

## 🔧 TROUBLESHOOTING GUIDE

### Issue 1: No Statistical Findings
**Symptoms:** Log shows "Found 0 statistical outliers" for all rules

**Diagnosis:**
```python
# Check if metrics are calculating
import pandas as pd
df_rules = pd.read_excel('config/ValidationRules_v1_Corrected.xlsx')
df_stat = df_rules[df_rules['validation_type'].isin(['outlier_iqr', 'outlier_zscore'])]
print(df_stat[['checkpoint_id', 'enabled', 'column_1', 'column_2']])
```

**Fixes:**
1. Verify `enabled = True` for statistical rules
2. Check column names are correct
3. Verify data files loaded properly
4. Add debug logging to metric collection

### Issue 2: Too Many Outliers
**Symptoms:** 50%+ of ULBs flagged as outliers

**Diagnosis:** Sensitivity too high

**Fixes:**
- IQR: Increase multiplier 1.5 → 2.0 → 3.0
- Z-score: Increase limit 2.0 → 2.5 → 3.0

### Issue 3: Wrong Peer Groups
**Symptoms:** Groups don't make sense (e.g., all ULBs in one group)

**Diagnosis:**
```python
# Check population distribution
df = pd.read_csv('data/mp_270126_p1_1_1_2.csv')
print(df['p1_1_3_4_tot_25_no'].describe())
```

**Fixes:**
- Adjust population brackets to match actual distribution
- Use district grouping if population ranges unclear
- Check grade extraction is working

### Issue 4: Threshold Rules Broken
**Symptoms:** Existing rules that worked before now fail

**Diagnosis:** Check if threshold logic was accidentally modified

**Fix:** Restore from backup, verify threshold methods unchanged

### Issue 5: Performance Issues
**Symptoms:** Audit takes much longer than before

**Diagnosis:**
```python
import cProfile
cProfile.run('execute_all_ulbs()', 'stats.prof')
```

**Fixes:**
- Cache peer groups (calculate once, reuse)
- Optimize metric collection loop
- Consider parallel processing

---

## 📊 SUCCESS METRICS

### Technical Metrics
- ✅ Audit completion: 100%
- ✅ Crash rate: 0%
- ✅ Statistical rule execution rate: 100%
- ✅ Average audit runtime: <2x previous time

### Quality Metrics
- ✅ Manual calculation verification: 100% match
- ✅ False positive rate: <10% (per audit team review)
- ✅ Actionable findings: >80%
- ✅ Peer groupings sensible: Per domain expert review

### Adoption Metrics
- ✅ Audit team using statistical findings: Yes
- ✅ New statistical rules added: >0 after first month
- ✅ System uptime: >95%

---

## 📚 REFERENCE DOCUMENTATION

**For Testing:**
- This document (PHASE_4_TESTING_DEPLOYMENT.md)
- PHASE_4_ENGINE_COMPLETE.md

**For Configuration:**
- PHASE_4_USAGE_GUIDE.md
- QUICK_REFERENCE.md
- PHASE_4_CONFIG_UPDATED.md

**For Technical Details:**
- rule_executor_phase4.py (source code)
- PHASE_4_CONFIG_EXTENSION.md

---

## ✅ FINAL CHECKLIST

### Pre-Production
- [ ] All unit tests passed
- [ ] Integration tests passed  
- [ ] Manual calculations verified
- [ ] Edge cases tested
- [ ] Documentation reviewed
- [ ] Backup created

### Production
- [ ] Files deployed
- [ ] Test run successful
- [ ] No errors in logs
- [ ] Reports generated correctly
- [ ] Team notified

### Post-Production
- [ ] Week 1 monitoring complete
- [ ] Feedback collected
- [ ] Tuning performed if needed
- [ ] Knowledge transfer done

---

**Document Version**: 1.0  
**Last Updated**: February 6, 2026  
**Status**: Ready for Production Deployment
