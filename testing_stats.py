"""
OH Stats Testing Script
=======================

Demonstrates the full statistical analysis pipeline for EMG data:
1. Data preparation
2. Descriptive statistics & QA
3. Model fitting (LMM)
4. Post-hoc contrasts
5. FDR correction
6. Diagnostics
7. Report generation

Run from the OH_Parser directory:
    python testing_stats.py
"""
import sys
import warnings

# Suppress some convergence warnings for cleaner output
warnings.filterwarnings("ignore", category=RuntimeWarning)

from oh_parser import load_profiles, list_subjects

# =============================================================================
# SETUP: Load profiles
# =============================================================================
print("=" * 70)
print("OH STATS PIPELINE DEMONSTRATION")
print("=" * 70)

OH_PROFILES_PATH = "/Volumes/NO NAME/Backup PrevOccupAI_PLUS Data/OH_profiles"

print("\n[1] Loading OH profiles...")
profiles = load_profiles(OH_PROFILES_PATH)
subjects = list_subjects(profiles)
print(f"    Loaded {len(subjects)} subjects: {subjects[:5]}...")

# =============================================================================
# STEP 1: Data Preparation
# =============================================================================
print("\n" + "=" * 70)
print("[2] DATA PREPARATION")
print("=" * 70)

from oh_stats import prepare_daily_emg, prepare_daily_questionnaires

# Prepare daily EMG data (keep both sides)
ds = prepare_daily_emg(profiles, side="both")
print(f"\nDataset summary:")
print(f"  Shape: {ds['data'].shape}")
print(f"  Outcomes: {len(ds['outcome_vars'])} variables")
print(f"  ID var: {ds['id_var']}")
print(f"  Time var: {ds['time_var']}")
print(f"  Grouping: {ds['grouping_vars']}")
print(f"\nFirst 10 rows:")
print(ds['data'].head(10).to_string())

# Check if questionnaire data is available (conditionally activated)
qs = prepare_daily_questionnaires(profiles)
if qs is None:
    print("\n[Note] Daily questionnaire data not available - skipping")
else:
    print(f"\nQuestionnaire data: {qs['data'].shape}")

# =============================================================================
# STEP 2: Descriptive Statistics
# =============================================================================
print("\n" + "=" * 70)
print("[3] DESCRIPTIVE STATISTICS")
print("=" * 70)

from oh_stats import summarize_outcomes, check_normality, check_variance, missingness_report

# Select key outcomes for demonstration
primary_outcomes = [
    "EMG_intensity.mean_percent_mvc",
    "EMG_apdf.active.p50",
    "EMG_rest_recovery.rest_percent",
    "EMG_rest_recovery.gap_count",
]

# Summary statistics
print("\n--- Summary Statistics ---")
summary = summarize_outcomes(ds, outcomes=primary_outcomes)
print(summary.to_string(index=False))

# Normality check
print("\n--- Normality Assessment ---")
normality = check_normality(ds, outcomes=primary_outcomes)
print(normality[["outcome", "n", "skewness", "is_normal", "recommended_transform"]].to_string(index=False))

# Variance check (detect degenerate outcomes)
print("\n--- Variance Check (Degenerate Detection) ---")
variance = check_variance(ds, outcomes=primary_outcomes)
print(variance[["outcome", "n_unique", "pct_mode", "is_degenerate", "reason"]].to_string(index=False))

# Missingness
print("\n--- Missingness Summary ---")
miss = missingness_report(ds, outcomes=primary_outcomes)
print(f"Total missing: {miss['summary']['total_missing']} cells ({miss['summary']['pct_missing']:.1f}%)")

# =============================================================================
# STEP 3: Fit Linear Mixed Models
# =============================================================================
print("\n" + "=" * 70)
print("[4] LINEAR MIXED MODELS")
print("=" * 70)

from oh_stats import fit_lmm, fit_all_outcomes, summarize_lmm_result
from oh_stats.registry import get_outcome_info, OutcomeType

# Fit single model (primary outcome)
print("\n--- Single Model: EMG Mean %MVC ---")
result = fit_lmm(
    ds,
    outcome="EMG_intensity.mean_percent_mvc",
    fixed_effects=["C(day_index)", "C(side)"],  # Day + Side as categorical
    random_intercept="subject_id",
)
print(summarize_lmm_result(result))
print("\nCoefficients:")
print(result['coefficients'].to_string(index=False))

# Check model fit stats
print(f"\nRandom effects:")
group_var = result['random_effects'].get('group_var', 'NA')
resid_var = result['random_effects'].get('residual_var', 'NA')
icc = result['random_effects'].get('icc', 'NA')
print(f"  Subject variance: {group_var:.4f}" if isinstance(group_var, (int, float)) else f"  Subject variance: {group_var}")
print(f"  Residual variance: {resid_var:.4f}" if isinstance(resid_var, (int, float)) else f"  Residual variance: {resid_var}")
print(f"  ICC: {icc:.3f}" if isinstance(icc, (int, float)) else f"  ICC: {icc}")

# =============================================================================
# STEP 4: Fit Multiple Outcomes
# =============================================================================
print("\n" + "=" * 70)
print("[5] BATCH MODEL FITTING")
print("=" * 70)

# Get non-degenerate continuous outcomes
from oh_stats.descriptive import get_non_degenerate_outcomes
from oh_stats.registry import list_outcomes

continuous_outcomes = list_outcomes(outcome_type=OutcomeType.CONTINUOUS)
print(f"\nRegistered continuous outcomes: {len(continuous_outcomes)}")

# Filter to non-degenerate
valid_outcomes = get_non_degenerate_outcomes(ds, continuous_outcomes[:10])  # Limit for demo
print(f"Non-degenerate outcomes: {len(valid_outcomes)}")

# Fit all
results = fit_all_outcomes(ds, outcomes=valid_outcomes[:5], skip_degenerate=True)
print(f"\nFitted {len(results)} models")

for name, r in results.items():
    status = "✓" if r['converged'] else "✗"
    aic = r['fit_stats'].get('aic', 'NA')
    icc_val = r['random_effects'].get('icc', 'NA')
    aic_str = f"{aic:.1f}" if isinstance(aic, (int, float)) else str(aic)
    icc_str = f"{icc_val:.3f}" if isinstance(icc_val, (int, float)) else str(icc_val)
    print(f"  {status} {name}: AIC={aic_str}, ICC={icc_str}")

# =============================================================================
# STEP 5: Post-hoc Contrasts
# =============================================================================
print("\n" + "=" * 70)
print("[6] POST-HOC CONTRASTS")
print("=" * 70)

from oh_stats import pairwise_contrasts, compute_emmeans, summarize_contrast_result

# Pairwise day comparisons for primary outcome
result_main = results.get("EMG_intensity.mean_percent_mvc")
if result_main and result_main['converged']:
    print("\n--- Pairwise Day Contrasts: EMG Mean %MVC ---")
    contrasts_df = pairwise_contrasts(result_main, factor="day_index", ds=ds, correction="holm")
    print("\nPairwise Contrasts (Holm-corrected):")
    print(contrasts_df[["contrast", "estimate", "std_error", "p_adjusted"]].head(10).to_string(index=False))
    
    print("\nEstimated Marginal Means:")
    emmeans_df = compute_emmeans(result_main, factor="day_index", ds=ds)
    print(emmeans_df.to_string(index=False))

# =============================================================================
# STEP 6: FDR Correction Across Outcomes
# =============================================================================
print("\n" + "=" * 70)
print("[7] MULTIPLICITY CORRECTION (FDR)")
print("=" * 70)

from oh_stats import apply_fdr, apply_holm

# Apply FDR correction for day_index effect across outcomes
fdr_results = apply_fdr(results, term="day_index", method="fdr_bh")

print("\n--- FDR Results (Benjamini-Hochberg) ---")
print(fdr_results[["outcome", "p_raw", "p_adjusted", "significant"]].to_string(index=False))

# Summary
n_sig = fdr_results['significant'].sum()
n_total = len(fdr_results)
print(f"\nSignificant outcomes: {n_sig}/{n_total} (FDR < 0.05)")

# =============================================================================
# STEP 7: Model Diagnostics
# =============================================================================
print("\n" + "=" * 70)
print("[8] MODEL DIAGNOSTICS")
print("=" * 70)

from oh_stats import residual_diagnostics, check_assumptions, summarize_diagnostics

if result_main and result_main['converged']:
    print("\n--- Diagnostics: EMG Mean %MVC ---")
    diag = residual_diagnostics(result_main)
    print(summarize_diagnostics(diag))
    
    print("\nResidual Normality:")
    print(f"  Shapiro-Wilk p: {diag['normality_p']:.4f}")
    
    print("\nOutliers:")
    print(f"  Count: {diag['n_outliers']}")

# =============================================================================
# STEP 8: Report Generation
# =============================================================================
print("\n" + "=" * 70)
print("[9] REPORT GENERATION")
print("=" * 70)

from oh_stats import descriptive_table, coefficient_table, results_summary

# Table 1 style
print("\n--- Table 1: Descriptive Statistics ---")
table1 = descriptive_table(ds, outcomes=primary_outcomes[:3])
print(table1.to_string(index=False))

# Coefficient table
if result_main and result_main['converged']:
    print("\n--- Coefficient Table ---")
    coef_table = coefficient_table(result_main)
    print(coef_table.to_string(index=False))

# Results summary
print("\n--- Results Summary ---")
res_summary = results_summary(results, fdr_results)
print(res_summary.to_string(index=False))

# =============================================================================
# STEP 9: Registry Demonstration
# =============================================================================
print("\n" + "=" * 70)
print("[10] OUTCOME REGISTRY")
print("=" * 70)

from oh_stats.registry import (
    list_outcomes, get_outcome_info, register_outcome,
    OutcomeType, AnalysisLevel, TransformType
)

print("\n--- Registry Contents ---")
print(f"Total registered outcomes: {len(list_outcomes())}")
print(f"Continuous: {len(list_outcomes(outcome_type=OutcomeType.CONTINUOUS))}")
print(f"Proportion: {len(list_outcomes(outcome_type=OutcomeType.PROPORTION))}")
print(f"Count: {len(list_outcomes(outcome_type=OutcomeType.COUNT))}")
print(f"Primary: {len(list_outcomes(primary_only=True))}")

# Show info for a specific outcome
info = get_outcome_info("EMG_apdf.active.p50")
print(f"\n--- Outcome Info: EMG_apdf.active.p50 ---")
if info:
    print(f"  Type: {info['outcome_type'].name}")
    print(f"  Level: {info['level']}")
    print(f"  Transform: {info['transform'].name}")
    print(f"  Is Primary: {info.get('is_primary', False)}")
    print(f"  Description: {info.get('description', 'N/A')}")
else:
    print("  (Not found in registry)")

# =============================================================================
# DONE
# =============================================================================
print("\n" + "=" * 70)
print("PIPELINE DEMONSTRATION COMPLETE")
print("=" * 70)
print("""
Next steps:
1. Examine degenerate outcomes (check_variance) before modeling
2. Consider transforms for skewed outcomes (check_normality)
3. Run full analysis on all valid outcomes (fit_all_outcomes)
4. Apply FDR correction across outcomes (apply_fdr)
5. Run post-hoc contrasts for significant outcomes (pairwise_contrasts)
6. Generate publication-ready tables (descriptive_table, coefficient_table)
7. Export results (export_to_csv, export_to_latex)
""")
