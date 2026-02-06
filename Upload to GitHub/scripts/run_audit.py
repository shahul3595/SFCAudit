"""
ULB Audit Framework - Main Execution Script
Tamil Nadu State Finance Commission - Municipality Questionnaire Audit System

This script orchestrates the complete audit workflow:
1. Load validation rules from Excel
2. Load ULB data from CSV files
3. Execute all validation rules
4. Generate individual ULB reports (PDF)
5. Generate master dashboard (Excel)
"""

import pandas as pd
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_loader import DataLoader
from rule_executor import RuleExecutor
from report_generator import ReportGenerator

def setup_logging(log_folder):
    """Setup logging configuration"""
    log_folder = Path(log_folder)
    log_folder.mkdir(parents=True, exist_ok=True)
    
    log_file = log_folder / f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def main():
    """Main execution function"""
    
    # Setup paths
    base_dir = Path(__file__).parent.parent
    config_dir = base_dir / 'config'
    data_dir = base_dir / 'data'
    reports_dir = base_dir / 'reports'
    logs_dir = base_dir / 'logs'
    
    # Create directories if they don't exist
    for directory in [config_dir, data_dir, reports_dir, logs_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Setup logging
    logger = setup_logging(logs_dir)
    
    logger.info("="*80)
    logger.info("ULB AUDIT FRAMEWORK - Tamil Nadu State Finance Commission")
    logger.info("="*80)
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Base Directory: {base_dir}")
    logger.info(f"Data Directory: {data_dir}")
    logger.info(f"Reports Directory: {reports_dir}")
    
    try:
        # ====================================================================
        # STEP 1: Load Validation Rules
        # ====================================================================
        logger.info("\n" + "="*80)
        logger.info("STEP 1: Loading Validation Rules")
        logger.info("="*80)
        
        rules_file = config_dir / 'ValidationRules_v1_Corrected.xlsx'
        if not rules_file.exists():
            logger.error(f"Validation rules file not found: {rules_file}")
            logger.error("Please ensure ValidationRules_v1_Corrected.xlsx is in the config folder")
            return
        
        df_rules = pd.read_excel(rules_file, sheet_name='ValidationRules')
        enabled_rules = df_rules[df_rules['enabled'] == True]
        logger.info(f"[OK] Loaded {len(df_rules)} total rules")
        logger.info(f"[OK] {len(enabled_rules)} rules are enabled")
        
        # ====================================================================
        # STEP 2: Load ULB Data
        # ====================================================================
        logger.info("\n" + "="*80)
        logger.info("STEP 2: Loading ULB Data from CSV Files")
        logger.info("="*80)
        
        if not data_dir.exists() or not any(data_dir.iterdir()):
            logger.error(f"Data directory is empty: {data_dir}")
            logger.error("Please place all CSV files in the 'data' folder")
            return
        
        data_loader = DataLoader(data_dir)
        data = data_loader.load_all_data()
        
        if not data_loader.ulb_list:
            logger.error("No ULBs found in data. Please check Part 1 CSV file.")
            return
        
        logger.info(f"[OK] Loaded {len(data)} tables")
        logger.info(f"[OK] Found {len(data_loader.ulb_list)} ULBs")
        
        # ====================================================================
        # STEP 3: Execute Validation Rules
        # ====================================================================
        logger.info("\n" + "="*80)
        logger.info("STEP 3: Executing Validation Rules")
        logger.info("="*80)
        
        rule_executor = RuleExecutor(df_rules, data_loader)
        all_findings = rule_executor.execute_all_ulbs()
        
        logger.info(f"[OK] Audit execution complete")
        logger.info(f"[OK] Total findings: {len(all_findings)}")
        
        if all_findings:
            severity_counts = {}
            for f in all_findings:
                sev = f['severity']
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            logger.info("\nFindings by Severity:")
            for sev in ['Critical', 'High', 'Medium', 'Low']:
                if sev in severity_counts:
                    logger.info(f"  • {sev}: {severity_counts[sev]}")
        
        # ====================================================================
        # STEP 4: Generate Individual ULB Reports
        # ====================================================================
        logger.info("\n" + "="*80)
        logger.info("STEP 4: Generating Individual ULB Reports (PDF)")
        logger.info("="*80)
        
        report_generator = ReportGenerator(reports_dir)
        
        ulb_reports_generated = 0
        for ulb in data_loader.ulb_list:
            mp_id = ulb['mp_id']
            ulb_findings = [f for f in all_findings if f['mp_id'] == mp_id]
            
            try:
                report_generator.generate_ulb_report(mp_id, ulb, ulb_findings)
                ulb_reports_generated += 1
            except Exception as e:
                logger.error(f"Failed to generate report for {ulb['municipality_name']}: {str(e)}")
        
        logger.info(f"[OK] Generated {ulb_reports_generated} ULB reports")
        
        # ====================================================================
        # STEP 5: Generate Master Dashboard
        # ====================================================================
        logger.info("\n" + "="*80)
        logger.info("STEP 5: Generating Master Dashboard (Excel)")
        logger.info("="*80)
        
        dashboard_path = report_generator.generate_master_dashboard(all_findings, data_loader)
        logger.info(f"[OK] Master dashboard: {dashboard_path.name}")
        
        detailed_path = report_generator.generate_master_tabular_report(all_findings, data_loader)
        logger.info(f"[OK] Detailed report: {detailed_path.name}")
        
        # ====================================================================
        # COMPLETION
        # ====================================================================
        logger.info("\n" + "="*80)
        logger.info("AUDIT FRAMEWORK EXECUTION COMPLETE")
        logger.info("="*80)
        logger.info(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"\nAll reports saved to: {reports_dir}")
        logger.info("\nSUMMARY:")
        logger.info(f"  • ULBs Processed: {len(data_loader.ulb_list)}")
        logger.info(f"  • Total Findings: {len(all_findings)}")
        logger.info(f"  • Individual Reports: {ulb_reports_generated}")
        logger.info(f"  • Master Dashboard: 1")
        logger.info(f"  • Detailed Report: 1")
        logger.info("\n[OK] Audit execution successful!")
        
    except Exception as e:
        logger.error(f"\n[ERROR] FATAL ERROR: {str(e)}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())