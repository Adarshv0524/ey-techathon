import logging
from datetime import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
import os
from app.config import settings

logger = logging.getLogger(__name__)


class LoanDocumentGenerator:
    """Generate professional loan approval/rejection documents"""
    
    def __init__(self):
        self.output_dir = settings.OUTPUT_PDF_DIR
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Custom Title
        if 'CustomTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a5490'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ))
        
        # Section Header
        if 'SectionHeader' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionHeader',
                parent=self.styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#2c5aa0'),
                spaceAfter=12,
                spaceBefore=12,
                fontName='Helvetica-Bold'
            ))
        
        # Custom Body Text
        if 'CustomBody' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomBody',
                parent=self.styles['Normal'],
                fontSize=11,
                spaceAfter=8,
                alignment=TA_LEFT
            ))
        
        # Footer Text
        if 'FooterText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='FooterText',
                parent=self.styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                alignment=TA_CENTER
            ))
    
    def generate_approval_letter(
        self,
        session_data: Dict[str, Any],
        underwriting_result: Dict[str, Any]
    ) -> str:
        """
        Generate loan approval letter PDF
        
        Returns:
            Path to generated PDF file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            customer_id = session_data.get("customer_id", "UNKNOWN")
            filename = f"loan_approval_{customer_id}_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                filepath,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=1*inch,
                bottomMargin=0.75*inch
            )
            
            story = []
            
            # Company Header
            story.append(Paragraph(settings.COMPANY_NAME, self.styles['CustomTitle']))
            story.append(Paragraph(
                f"{settings.COMPANY_ADDRESS}<br/>"
                f"Phone: {settings.COMPANY_PHONE} | Email: {settings.COMPANY_EMAIL}",
                self.styles['FooterText']
            ))
            story.append(Spacer(1, 0.3*inch))
            
            # Document Title
            story.append(Paragraph("LOAN APPROVAL LETTER", self.styles['CustomTitle']))
            story.append(Spacer(1, 0.2*inch))
            
            # Reference Details
            ref_date = datetime.now().strftime("%B %d, %Y")
            ref_number = f"TIA/LA/{customer_id}/{timestamp}"
            
            story.append(Paragraph(f"<b>Date:</b> {ref_date}", self.styles['CustomBody']))
            story.append(Paragraph(f"<b>Reference No:</b> {ref_number}", self.styles['CustomBody']))
            story.append(Paragraph(f"<b>Customer ID:</b> {customer_id}", self.styles['CustomBody']))
            story.append(Spacer(1, 0.3*inch))
            
            # Greeting
            story.append(Paragraph("Dear Valued Customer,", self.styles['CustomBody']))
            story.append(Spacer(1, 0.1*inch))
            
            # Approval Message
            approval_text = f"""
            We are pleased to inform you that your personal loan application has been 
            <b>APPROVED</b>. After careful review of your application and supporting documents, 
            we are confident in extending the following loan facility to you.
            """
            story.append(Paragraph(approval_text, self.styles['CustomBody']))
            story.append(Spacer(1, 0.2*inch))
            
            # Loan Details Table
            story.append(Paragraph("LOAN DETAILS", self.styles['SectionHeader']))
            
            loan_amount = underwriting_result.get("approved_amount", 0)
            interest_rate = underwriting_result.get("interest_rate", 0)
            tenure_months = 36  # Default tenure
            monthly_emi = self._calculate_emi(loan_amount, interest_rate, tenure_months)
            
            loan_details_data = [
                ["Particulars", "Details"],
                ["Approved Loan Amount", f"₹ {loan_amount:,.2f}"],
                ["Interest Rate (per annum)", f"{interest_rate}%"],
                ["Loan Tenure", f"{tenure_months} months"],
                ["Estimated Monthly EMI", f"₹ {monthly_emi:,.2f}"],
                ["Processing Fee", f"₹ {loan_amount * 0.02:,.2f} (2%)"],
                ["Total Amount Payable", f"₹ {monthly_emi * tenure_months:,.2f}"]
            ]
            
            loan_table = Table(loan_details_data, colWidths=[3*inch, 3*inch])
            loan_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5490')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(loan_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Terms and Conditions
            story.append(Paragraph("TERMS & CONDITIONS", self.styles['SectionHeader']))
            terms = [
                "The loan amount will be disbursed within 2-3 business days after document verification.",
                "EMI payments must be made on or before the 5th of each month.",
                "Late payment charges of 2% per month will apply on overdue amounts.",
                "The loan is subject to final verification of documents and credit check.",
                "Please review the detailed loan agreement document for complete terms.",
            ]
            
            for i, term in enumerate(terms, 1):
                story.append(Paragraph(f"{i}. {term}", self.styles['CustomBody']))
            
            story.append(Spacer(1, 0.3*inch))
            
            # Next Steps
            story.append(Paragraph("NEXT STEPS", self.styles['SectionHeader']))
            next_steps_text = """
            Our loan specialist will contact you within 24 hours to complete the documentation 
            process. Please keep the following documents ready:
            <br/><br/>
            • Original identity proof (Aadhaar/PAN)<br/>
            • Address proof<br/>
            • Last 6 months bank statements<br/>
            • Recent salary slips<br/>
            """
            story.append(Paragraph(next_steps_text, self.styles['CustomBody']))
            story.append(Spacer(1, 0.3*inch))
            
            # Closing
            closing_text = """
            We appreciate your trust in TIA Personal Loans. Should you have any questions, 
            please feel free to contact us at the above-mentioned contact details.
            """
            story.append(Paragraph(closing_text, self.styles['CustomBody']))
            story.append(Spacer(1, 0.2*inch))
            
            story.append(Paragraph("Warm Regards,<br/><br/>", self.styles['CustomBody']))
            story.append(Paragraph("<b>TIA Personal Loans</b><br/>Loan Processing Team", self.styles['CustomBody']))
            
            # Footer
            story.append(Spacer(1, 0.5*inch))
            footer_text = f"""
            <i>This is a system-generated document. For queries, contact {settings.COMPANY_EMAIL}</i>
            """
            story.append(Paragraph(footer_text, self.styles['FooterText']))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Generated approval letter: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Error generating approval letter: {e}", exc_info=True)
            raise
    
    def generate_rejection_letter(
        self,
        session_data: Dict[str, Any],
        underwriting_result: Dict[str, Any]
    ) -> str:
        """
        Generate loan rejection letter PDF
        
        Returns:
            Path to generated PDF file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            customer_id = session_data.get("customer_id", "UNKNOWN")
            filename = f"loan_decision_{customer_id}_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            doc = SimpleDocTemplate(
                filepath,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=1*inch,
                bottomMargin=0.75*inch
            )
            
            story = []
            
            # Company Header
            story.append(Paragraph(settings.COMPANY_NAME, self.styles['CustomTitle']))
            story.append(Paragraph(
                f"{settings.COMPANY_ADDRESS}<br/>"
                f"Phone: {settings.COMPANY_PHONE} | Email: {settings.COMPANY_EMAIL}",
                self.styles['FooterText']
            ))
            story.append(Spacer(1, 0.3*inch))
            
            # Document Title
            story.append(Paragraph("LOAN APPLICATION STATUS", self.styles['CustomTitle']))
            story.append(Spacer(1, 0.2*inch))
            
            # Reference Details
            ref_date = datetime.now().strftime("%B %d, %Y")
            ref_number = f"TIA/LS/{customer_id}/{timestamp}"
            
            story.append(Paragraph(f"<b>Date:</b> {ref_date}", self.styles['CustomBody']))
            story.append(Paragraph(f"<b>Reference No:</b> {ref_number}", self.styles['CustomBody']))
            story.append(Paragraph(f"<b>Customer ID:</b> {customer_id}", self.styles['CustomBody']))
            story.append(Spacer(1, 0.3*inch))
            
            # Greeting
            story.append(Paragraph("Dear Valued Customer,", self.styles['CustomBody']))
            story.append(Spacer(1, 0.1*inch))
            
            # Status Message
            reason = underwriting_result.get("reason", "eligibility criteria not met")
            status_text = f"""
            Thank you for applying for a personal loan with {settings.COMPANY_NAME}. 
            After careful evaluation of your application, we regret to inform you that 
            we are unable to approve your loan request at this time.
            <br/><br/>
            <b>Reason:</b> {reason}
            """
            story.append(Paragraph(status_text, self.styles['CustomBody']))
            story.append(Spacer(1, 0.3*inch))
            
            # Recommendations
            story.append(Paragraph("RECOMMENDATIONS", self.styles['SectionHeader']))
            recommendations = [
                "Improve your credit score by ensuring timely payment of existing loans/credit cards.",
                "Reduce existing debt obligations to improve debt-to-income ratio.",
                "Maintain stable employment and income documentation.",
                "Consider applying for a lower loan amount that aligns with your current income.",
                "You may reapply after 3 months with updated documentation.",
            ]
            
            for i, rec in enumerate(recommendations, 1):
                story.append(Paragraph(f"{i}. {rec}", self.styles['CustomBody']))
            
            story.append(Spacer(1, 0.3*inch))
            
            # Alternative Options
            story.append(Paragraph("ALTERNATIVE OPTIONS", self.styles['SectionHeader']))
            alternatives_text = """
            We encourage you to explore our other financial products that might be more 
            suitable for your current profile:
            <br/><br/>
            • Secured Loans (with collateral)<br/>
            • Credit Builder Program<br/>
            • Pre-approved Credit Cards<br/>
            """
            story.append(Paragraph(alternatives_text, self.styles['CustomBody']))
            story.append(Spacer(1, 0.3*inch))
            
            # Closing
            closing_text = """
            We value your interest in our services. For personalized guidance or to discuss 
            alternative options, please contact our customer support team.
            """
            story.append(Paragraph(closing_text, self.styles['CustomBody']))
            story.append(Spacer(1, 0.2*inch))
            
            story.append(Paragraph("Warm Regards,<br/><br/>", self.styles['CustomBody']))
            story.append(Paragraph("<b>TIA Personal Loans</b><br/>Credit Assessment Team", self.styles['CustomBody']))
            
            # Footer
            story.append(Spacer(1, 0.5*inch))
            footer_text = f"""
            <i>This is a system-generated document. For queries, contact {settings.COMPANY_EMAIL}</i>
            """
            story.append(Paragraph(footer_text, self.styles['FooterText']))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Generated decision letter: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Error generating rejection letter: {e}", exc_info=True)
            raise
    
    def _calculate_emi(self, principal: float, annual_rate: float, tenure_months: int) -> float:
        """Calculate EMI using reducing balance method"""
        monthly_rate = annual_rate / (12 * 100)
        
        if monthly_rate == 0:
            return principal / tenure_months
        
        emi = principal * monthly_rate * (
            (1 + monthly_rate) ** tenure_months
        ) / (
            ((1 + monthly_rate) ** tenure_months) - 1
        )
        
        return round(emi, 2)


# Global instance
pdf_generator = LoanDocumentGenerator()
