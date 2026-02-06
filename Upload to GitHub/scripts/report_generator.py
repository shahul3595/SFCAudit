"""
ULB Audit Framework - Report Generator (with Timestamped Folders)
- Creates timestamped subfolder for each audit run
- Prevents report flooding in base folder
"""

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import logging
from pathlib import Path

class ReportGenerator:
    """Generates audit reports in timestamped folders"""
    
    def __init__(self, output_folder):
        # Create timestamped subfolder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_folder = Path(output_folder) / f"Audit_{timestamp}"
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Reports will be saved to: {self.output_folder}")
        self.column_map = self._load_column_map()

    def _load_column_map(self):
        """Load optional column label/section mapping from mp-map.xlsx."""
        map_path = Path(__file__).resolve().parents[2] / 'mp-map.xlsx'
        if not map_path.exists():
            self.logger.warning("mp-map.xlsx not found. Reports will show raw column names only.")
            return {}

        try:
            df = pd.read_excel(map_path, sheet_name='consolidated', header=None)
            mapping = {}
            for _, row in df.iterrows():
                col_key = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
                if not col_key:
                    continue
                section = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
                label = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''
                mapping[col_key] = {
                    'section': section,
                    'label': label,
                }
            self.logger.info(f"[OK] Loaded {len(mapping)} column mappings from mp-map.xlsx")
            return mapping
        except Exception as e:
            self.logger.warning(f"Unable to load mp-map.xlsx: {str(e)}")
            return {}

    def _format_column_reference(self, column_name):
        if pd.isna(column_name) or str(column_name).strip() == '':
            return ''
        column_name = str(column_name).strip()
        map_item = self.column_map.get(column_name, {})
        label = map_item.get('label')
        section = map_item.get('section')
        parts = [f"{column_name}"]
        if label:
            parts.append(label)
        if section:
            parts.append(f"Section: {section}")
        return " | ".join(parts)

    def _build_user_friendly_observation(self, finding):
        col1 = self._format_column_reference(finding.get('column_1'))
        col2 = self._format_column_reference(finding.get('column_2'))
        refs = []
        if col1:
            refs.append(f"Primary field: {col1}")
        if col2:
            refs.append(f"Reference field: {col2}")

        detail = str(finding.get('detail', ''))
        if detail.startswith('Cross-table:'):
            detail = detail.replace('Cross-table:', 'Cross-table comparison failed:', 1)
        elif detail.startswith('Unable to evaluate:'):
            detail = detail.replace('Unable to evaluate:', 'Could not evaluate this check:', 1)

        if refs:
            detail = f"{detail}<br/><b>Fields:</b><br/>" + "<br/>".join(refs)
        return detail
        
    def generate_ulb_report(self, mp_id, ulb_info, findings):
        """Generate individual ULB audit report PDF"""
        filename = f"Audit_Report_{ulb_info['municipality_name'].replace(' ', '_')}_ID{mp_id}.pdf"
        filepath = self.output_folder / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=A4,
                               topMargin=0.5*inch, bottomMargin=0.5*inch,
                               leftMargin=0.5*inch, rightMargin=0.5*inch)
        
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2e5c8a'),
            spaceAfter=6,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        story.append(Paragraph("TAMIL NADU STATE FINANCE COMMISSION", title_style))
        story.append(Paragraph("ULB Questionnaire Audit Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        ulb_info_data = [
            ["Municipality", ulb_info['municipality_name']],
            ["District", ulb_info['district_name']],
            ["ULB ID", str(mp_id)],
            ["Report Date", datetime.now().strftime("%d-%b-%Y")],
        ]
        
        ulb_table = Table(ulb_info_data, colWidths=[2*inch, 4*inch])
        ulb_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(ulb_table)
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
        
        if not findings:
            story.append(Paragraph("No audit observations found. All validations passed successfully.", 
                                 styles['Normal']))
        else:
            severity_counts = {}
            for f in findings:
                sev = f['severity']
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            summary_text = f"Total Observations: {len(findings)}<br/>"
            for sev in ['Critical', 'High', 'Medium', 'Low']:
                if sev in severity_counts:
                    summary_text += f"• {sev} Priority: {severity_counts[sev]}<br/>"
            
            story.append(Paragraph(summary_text, styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        if findings:
            story.append(Paragraph("DETAILED OBSERVATIONS", heading_style))
            
            findings_by_part = {}
            for f in findings:
                part = f['part_no']
                if part not in findings_by_part:
                    findings_by_part[part] = []
                findings_by_part[part].append(f)
            
            def part_sort_key(part_str):
                try:
                    return int(str(part_str).split(',')[0])
                except:
                    return 999
            
            for part in sorted(findings_by_part.keys(), key=part_sort_key):
                part_findings = findings_by_part[part]
                
                part_names = {
                    '1': 'PART I - DEMOGRAPHICS AND GEOGRAPHY',
                    '2': 'PART II - HUMAN RESOURCES',
                    '3': 'PART III - ACCOUNTS',
                    '4': 'PART IV - TAXATION AND DCB',
                    '5': 'PART V - LIABILITIES',
                    '6': 'PART VI - CAPITAL WORKS',
                    '7': 'PART VII - ASSETS',
                    '8': 'PART VIII - SERVICE LEVELS',
                    '9': 'PART IX - FUTURE NEEDS',
                }
                
                part_name = part_names.get(str(part), f'PART {part}')
                story.append(Paragraph(part_name, heading_style))
                
                table_data = [['#', 'Rule', 'Severity', 'Observation']]
                
                for idx, f in enumerate(part_findings, 1):
                    obs_text = f"{f['description']}<br/><b>Finding:</b> {self._build_user_friendly_observation(f)}"
                    table_data.append([
                        str(idx),
                        f['rule_id'],
                        f['severity'],
                        Paragraph(obs_text, styles['Normal'])
                    ])
                
                findings_table = Table(table_data, colWidths=[0.3*inch, 0.8*inch, 0.8*inch, 5*inch])
                
                table_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]
                
                for idx in range(1, len(table_data)):
                    severity = table_data[idx][2]
                    severity_color = {
                        'Critical': colors.HexColor('#ff0000'),
                        'High': colors.HexColor('#ffc000'),
                        'Medium': colors.HexColor('#ffff00'),
                        'Low': colors.HexColor('#92d050')
                    }.get(severity, colors.white)
                    table_style.append(('BACKGROUND', (2, idx), (2, idx), severity_color))
                
                findings_table.setStyle(TableStyle(table_style))
                story.append(findings_table)
                story.append(Spacer(1, 0.2*inch))
        
        story.append(Spacer(1, 0.3*inch))
        footer_text = """
        <para align=justify>
        <b>Note:</b> This audit report is generated automatically based on validation rules applied to the 
        ULB questionnaire data. All findings should be reviewed and verified.
        </para>
        """
        story.append(Paragraph(footer_text, styles['Normal']))
        
        doc.build(story)
        self.logger.info(f"[OK] Generated report: {filename}")
        return filepath
    
    def generate_master_dashboard(self, all_findings, data_loader):
        """Generate master dashboard Excel"""
        filepath = self.output_folder / f"Master_Audit_Dashboard.xlsx"
        
        with pd.ExcelWriter(str(filepath), engine='openpyxl') as writer:
            summary_data = []
            for ulb in data_loader.ulb_list:
                mp_id = ulb['mp_id']
                ulb_findings = [f for f in all_findings if f['mp_id'] == mp_id]
                
                severity_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
                for f in ulb_findings:
                    sev = f['severity']
                    if sev in severity_counts:
                        severity_counts[sev] += 1
                
                summary_data.append({
                    'ULB_ID': mp_id,
                    'Municipality': ulb['municipality_name'],
                    'District': ulb['district_name'],
                    'Total_Findings': len(ulb_findings),
                    'Critical': severity_counts['Critical'],
                    'High': severity_counts['High'],
                    'Medium': severity_counts['Medium'],
                    'Low': severity_counts['Low'],
                })
            
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
            
            if all_findings:
                df_findings = pd.DataFrame(all_findings)
                df_findings = df_findings[[
                    'mp_id', 'ulb_name', 'district', 'rule_id', 'part_no', 
                    'severity', 'check_type', 'description', 'detail'
                ]]
                df_findings.columns = [
                    'ULB_ID', 'Municipality', 'District', 'Rule_ID', 'Part', 
                    'Severity', 'Check_Type', 'Validation_Rule', 'Finding_Detail'
                ]
                df_findings.to_excel(writer, sheet_name='All_Findings', index=False)
                
                for sev in ['Critical', 'High']:
                    df_sev = df_findings[df_findings['Severity'] == sev]
                    if not df_sev.empty:
                        sheet_name = f'{sev}_Priority'
                        df_sev.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                df_empty = pd.DataFrame({'Message': ['No audit findings. All validations passed.']})
                df_empty.to_excel(writer, sheet_name='All_Findings', index=False)
        
        self.logger.info(f"[OK] Generated master dashboard: {filepath.name}")
        return filepath
    
    def generate_master_tabular_report(self, all_findings, data_loader):
        """Generate detailed tabular master report Excel"""
        filepath = self.output_folder / f"Master_Detailed_Report.xlsx"
        
        with pd.ExcelWriter(str(filepath), engine='openpyxl') as writer:
            if all_findings:
                df_all = pd.DataFrame(all_findings)
                
                def part_sort_key(part_str):
                    try:
                        return int(str(part_str))
                    except:
                        return 999
                
                for part_no in sorted(df_all['part_no'].unique(), key=part_sort_key):
                    df_part = df_all[df_all['part_no'] == part_no]
                    
                    df_output = df_part[[
                        'mp_id', 'ulb_name', 'district', 'rule_id', 
                        'severity', 'description', 'detail'
                    ]].copy()
                    
                    df_output.columns = [
                        'ULB_ID', 'Municipality', 'District', 'Rule_ID',
                        'Severity', 'Validation_Rule', 'Finding_Detail'
                    ]
                    
                    sheet_name = f'Part_{part_no}'[:31]
                    df_output.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                df_empty = pd.DataFrame({'Message': ['No audit findings. All validations passed.']})
                df_empty.to_excel(writer, sheet_name='Summary', index=False)
        
        self.logger.info(f"[OK] Generated detailed report: {filepath.name}")
        return filepath
