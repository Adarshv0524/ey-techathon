# tia_sales_simulation.py
"""
TIA-Sales Agentic AI System Simulation
Demonstrates complete loan origination workflow with visual agent orchestration
"""

import time
import sys
from datetime import datetime
from typing import Dict, Any, List

# Terminal colors
class Color:
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    
    # Background colors
    BG_GREEN = '\033[102m'
    BG_BLUE = '\033[104m'
    BG_YELLOW = '\033[103m'

def print_header():
    """Print TIA-Sales logo"""
    logo = f"""
    {Color.BLUE}{Color.BOLD}
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║         ████████╗██╗ █████╗        ███████╗ █████╗ ██╗     ███████╗║
    ║         ╚══██╔══╝██║██╔══██╗       ██╔════╝██╔══██╗██║     ██╔════╝║
    ║            ██║   ██║███████║ █████╗███████╗███████║██║     █████╗  ║
    ║            ██║   ██║██╔══██║ ╚════╝╚════██║██╔══██║██║     ██╔══╝  ║
    ║            ██║   ██║██║  ██║       ███████║██║  ██║███████╗███████╗║
    ║            ╚═╝   ╚═╝╚═╝  ╚═╝       ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝║
    ║                                                                   ║
    ║              🤖 Agentic AI Loan Origination System                ║
    ║                    Real-Time Demonstration                        ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    {Color.END}
    """
    print(logo)
    time.sleep(1)

def print_section(title, icon="━"):
    """Print section divider"""
    print(f"\n{Color.CYAN}{Color.BOLD}")
    print(f"\n{'='*75}")
    print(f"{icon*3} {title.upper()} {icon*3}".center(75))
    print(f"{'='*75}")
    print(f"{Color.END}")

def print_agent_start(agent_name, task):
    """Print when agent starts"""
    print(f"\n{Color.YELLOW}┌{'─'*70}┐")
    print(f"│ 🤖 AGENT ACTIVATED: {Color.BOLD}{agent_name}{Color.END}{Color.YELLOW}")
    print(f"│ 📋 Task: {task}")
    print(f"└{'─'*70}┘{Color.END}")

def print_agent_status(message, status="info"):
    """Print agent processing status"""
    icons = {
        "info": "ℹ️ ",
        "success": "✅",
        "warning": "⚠️ ",
        "error": "❌",
        "processing": "⚙️ "
    }
    colors = {
        "info": Color.CYAN,
        "success": Color.GREEN,
        "warning": Color.YELLOW,
        "error": Color.RED,
        "processing": Color.BLUE
    }
    icon = icons.get(status, "•")
    color = colors.get(status, Color.WHITE)
    print(f"{color}  {icon} {message}{Color.END}")
    
def print_agent_complete(agent_name, result):
    """Print when agent completes"""
    print(f"\n{Color.GREEN}└─ ✓ {Color.BOLD}{agent_name} COMPLETED{Color.END}")
    print(f"{Color.GREEN}   Result: {result}{Color.END}\n")

def animate_processing(duration=1.5, task="Processing"):
    """Show animated processing"""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        sys.stdout.write(f"\r{Color.BLUE}  {frames[i % len(frames)]} {task}...{Color.END}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write(f"\r{Color.GREEN}  ✓ {task} complete{Color.END}\n")

def print_data_box(title, data: Dict[str, Any], color=Color.BLUE):
    """Print structured data in a box"""
    print(f"\n{color}┌─ {title} {'─'*(60-len(title))}┐")
    for key, value in data.items():
        print(f"│ {Color.BOLD}{key}:{Color.END}{color} {value}")
    print(f"└{'─'*60}┘{Color.END}\n")

def simulate_input_guardrails(user_input: str):
    """Simulate input validation"""
    print_section("INPUT GUARDRAILS", "🛡️")
    print(f"{Color.WHITE}User Input: \"{user_input}\"{Color.END}")
    
    animate_processing(0.5, "Validating input")
    print_agent_status("Length check: PASSED", "success")
    print_agent_status("Injection patterns: None detected", "success")
    print_agent_status("Offensive content: Clean", "success")
    print_agent_status("Sanitization: Complete", "success")
    
    time.sleep(0.5)

def simulate_semantic_router(user_input: str):
    """Simulate semantic routing"""
    print_section("SEMANTIC ROUTER", "🧭")
    print_agent_start("Semantic Router", "Classify user intent")
    
    animate_processing(0.8, "Running HuggingFace LLM classification")
    
    print_agent_status("LLM Model: mistralai/Mistral-7B-Instruct-v0.3", "info")
    print_agent_status("Temperature: 0.1 (deterministic)", "info")
    
    time.sleep(0.3)
    
    intents = ["GREETING", "KNOWLEDGE_QUERY", "TASK_ACTION"]
    print(f"\n{Color.CYAN}  Evaluating possible intents:{Color.END}")
    for intent in intents:
        if intent == "TASK_ACTION":
            print(f"  {Color.GREEN}✓ {intent}: 95% confidence{Color.END}")
        else:
            print(f"  {Color.WHITE}  {intent}: 8% confidence{Color.END}")
    
    print_agent_complete("Semantic Router", "Intent: TASK_ACTION")
    time.sleep(0.5)

def simulate_context_manager(session_id: str):
    """Simulate session management"""
    print_section("CONTEXT MANAGER", "💾")
    
    session_data = {
        "Session ID": session_id,
        "Created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Current State": "GREETING",
        "Messages": "1",
        "Redis TTL": "3600s"
    }
    
    print_data_box("Session State", session_data, Color.CYAN)
    print_agent_status("Session cached in Redis", "success")
    time.sleep(0.5)

def simulate_master_agent():
    """Simulate master agent orchestration"""
    print_section("MASTER AGENT (DIALOGUE MANAGER)", "🧠")
    print(f"\n{Color.PURPLE}{Color.BOLD}  ╔══════════════════════════════════════════════════╗")
    print(f"  ║   MASTER AGENT ORCHESTRATOR                      ║")
    print(f"  ║   • Manages conversation flow                    ║")
    print(f"  ║   • Delegates to specialized workers            ║")
    print(f"  ║   • Maintains state machine                      ║")
    print(f"  ╚══════════════════════════════════════════════════╝{Color.END}\n")
    
    animate_processing(0.6, "Analyzing current state")
    print_agent_status("Current State: GREETING", "info")
    print_agent_status("Required Action: transition to CONSENT", "info")
    print_agent_status("Delegating to: Consent Worker", "processing")
    time.sleep(0.5)

def simulate_consent_worker():
    """Simulate consent collection"""
    print_section("WORKER: CONSENT AGENT", "✅")
    print_agent_start("Consent Worker", "Capture RBI-compliant consent")
    
    animate_processing(0.4, "Checking consent status")
    print_agent_status("Consent required: YES", "info")
    print_agent_status("Regulatory framework: RBI Guidelines 2023", "info")
    
    time.sleep(0.3)
    print(f"\n{Color.YELLOW}  Consent prompt generated:{Color.END}")
    print(f"  {Color.WHITE}\"I need your explicit consent to collect and process\"")
    print(f"  \"your financial data. Do you agree?\"{Color.END}\n")
    
    animate_processing(0.5, "Waiting for user response")
    print_agent_status("User response: 'Yes, I agree'", "success")
    print_agent_status("Consent captured: TRUE", "success")
    print_agent_status("Timestamp logged to MySQL", "success")
    
    slot_update = {"consent": True, "consent_timestamp": datetime.now().isoformat()}
    print_data_box("Slot Updated", slot_update, Color.GREEN)
    
    print_agent_complete("Consent Worker", "Consent granted, proceeding")
    time.sleep(0.5)

def simulate_kyc_worker():
    """Simulate KYC verification"""
    print_section("WORKER: KYC AGENT", "🔍")
    print_agent_start("KYC Worker", "Verify customer identity")
    
    animate_processing(0.5, "Extracting customer ID from message")
    print_agent_status("Slot Filler activated (LLM)", "processing")
    print_agent_status("Extracted: CUST987654321", "success")
    
    time.sleep(0.3)
    animate_processing(0.8, "Validating customer ID with database")
    print_agent_status("Database lookup: SUCCESS", "success")
    
    customer_data = {
        "Customer ID": "CUST987654321",
        "Name": "Adarsh Kumar Verma",
        "Credit Score": "750 (Excellent)",
        "Account Status": "Active",
        "Eligibility": "₹15,00,000 (max)"
    }
    print_data_box("Customer Profile", customer_data, Color.GREEN)
    
    print_agent_status("Credit bureau check complete", "success")
    print_agent_complete("KYC Worker", "Customer verified")
    time.sleep(0.5)

def simulate_amount_worker():
    """Simulate loan amount extraction"""
    print_section("WORKER: AMOUNT AGENT", "💰")
    print_agent_start("Amount Worker", "Extract and validate loan amount")
    
    animate_processing(0.5, "Parsing user message with LLM")
    print_agent_status("Input: '5 lakhs'", "info")
    print_agent_status("Extracted: ₹5,00,000", "success")
    
    time.sleep(0.3)
    animate_processing(0.4, "Validating against eligibility")
    print_agent_status("Min amount: ₹50,000 ✓", "success")
    print_agent_status("Max amount: ₹15,00,000 ✓", "success")
    print_agent_status("Within limits: YES", "success")
    
    loan_details = {
        "Requested Amount": "₹5,00,000",
        "Eligible": "YES",
        "Interest Rate": "10.5% p.a.",
        "Tenure": "60 months",
        "Estimated EMI": "₹10,624/month"
    }
    print_data_box("Loan Calculation", loan_details, Color.GREEN)
    
    print_agent_complete("Amount Worker", "Amount validated")
    time.sleep(0.5)

def simulate_document_worker():
    """Simulate document processing"""
    print_section("WORKER: DOCUMENT AGENT", "📄")
    print_agent_start("Document Worker", "Process uploaded documents with OCR")
    
    documents = ["Salary Slip", "PAN Card", "Aadhaar Card"]
    
    for doc in documents:
        print(f"\n{Color.BLUE}  Processing: {doc}{Color.END}")
        animate_processing(0.6, f"Running OCR on {doc}")
        
        if doc == "Salary Slip":
            print_agent_status("OCR Engine: Tesseract", "info")
            print_agent_status("Image preprocessing: Complete", "success")
            print_agent_status("Text extraction: Success", "success")
            
            ocr_result = {
                "Monthly Salary": "₹75,000",
                "Employment Type": "Permanent",
                "Company": "Tech Solutions Pvt Ltd",
                "Confidence": "98%"
            }
            print_data_box(f"{doc} - Extracted Data", ocr_result, Color.GREEN)
            
        elif doc == "PAN Card":
            print_agent_status("OCR + Computer Vision", "processing")
            print_agent_status("Pattern matching: PAN format", "success")
            pan_data = {
                "PAN Number": "ABCDE1234F",
                "Name Match": "✓ Verified",
                "Confidence": "99%"
            }
            print_data_box(f"{doc} - Extracted Data", pan_data, Color.GREEN)
            
        else:  # Aadhaar
            print_agent_status("Masked extraction (PII protection)", "info")
            aadhaar_data = {
                "Aadhaar (last 4)": "****5678",
                "Name Match": "✓ Verified",
                "Confidence": "97%"
            }
            print_data_box(f"{doc} - Extracted Data", aadhaar_data, Color.GREEN)
    
    print_agent_status("All documents processed successfully", "success")
    print_agent_complete("Document Worker", "OCR complete, data extracted")
    time.sleep(0.5)

def simulate_underwriting_worker():
    """Simulate underwriting decision"""
    print_section("WORKER: UNDERWRITING AGENT", "⚖️")
    print_agent_start("Underwriting Worker", "Evaluate loan eligibility")
    
    print(f"\n{Color.YELLOW}  ╔══════════════════════════════════════════════════╗")
    print(f"  ║   RULESENGINE: Deterministic Decision Logic     ║")
    print(f"  ║   (No Black-Box AI - Fully Explainable)         ║")
    print(f"  ╚══════════════════════════════════════════════════╝{Color.END}\n")
    
    checks = [
        ("Income Verification (3x rule)", "₹75,000 × 24 = ₹18,00,000 > ₹5,00,000", True),
        ("FOIR Calculation", "32% (within 40% limit)", True),
        ("Credit Bureau Score", "750 (Excellent, > 650 required)", True),
        ("Employment Stability", "5 years (> 2 years required)", True),
        ("Debt-to-Income Ratio", "28% (healthy, < 50%)", True),
        ("Document Authenticity", "98% avg confidence (> 60%)", True)
    ]
    
    for check_name, details, passed in checks:
        animate_processing(0.4, f"Checking: {check_name}")
        if passed:
            print_agent_status(f"{check_name}: PASSED", "success")
            print(f"  {Color.CYAN}    └─ {details}{Color.END}")
        else:
            print_agent_status(f"{check_name}: FAILED", "error")
            print(f"  {Color.RED}    └─ {details}{Color.END}")
    
    time.sleep(0.5)
    
    decision = {
        "Decision": "APPROVED ✅",
        "Reason": "All eligibility criteria met",
        "Approved Amount": "₹5,00,000",
        "Interest Rate": "10.5% p.a.",
        "Risk Category": "Low Risk"
    }
    print_data_box("Underwriting Decision", decision, Color.GREEN)
    
    print_agent_status("Decision logged to MySQL (audit trail)", "success")
    print_agent_complete("Underwriting Worker", "Loan APPROVED")
    time.sleep(0.5)

def simulate_decision_worker():
    """Simulate decision delivery and PDF generation"""
    print_section("WORKER: DECISION AGENT", "📋")
    print_agent_start("Decision Worker", "Generate sanction letter")
    
    animate_processing(0.6, "Calculating EMI schedule")
    print_agent_status("EMI: ₹10,624/month for 60 months", "success")
    
    animate_processing(0.8, "Generating PDF with ReportLab")
    print_agent_status("Template: Sanction Letter (A4)", "info")
    print_agent_status("Content: Loan terms, conditions, schedule", "info")
    print_agent_status("PDF generated: sanction_letter_CUST987654321.pdf", "success")
    
    time.sleep(0.3)
    
    print(f"\n{Color.GREEN}  ╔══════════════════════════════════════════════════╗")
    print(f"  ║   🎉  LOAN APPROVED!                             ║")
    print(f"  ║                                                  ║")
    print(f"  ║   Approved Amount: ₹5,00,000                     ║")
    print(f"  ║   Interest Rate: 10.5% p.a.                      ║")
    print(f"  ║   Monthly EMI: ₹10,624                           ║")
    print(f"  ║   Sanction Letter: Ready for download            ║")
    print(f"  ╚══════════════════════════════════════════════════╝{Color.END}\n")
    
    print_agent_complete("Decision Worker", "Sanction letter delivered")
    time.sleep(0.5)

def simulate_final_summary():
    """Show final system summary"""
    print_section("WORKFLOW COMPLETE", "🎊")
    
    print(f"\n{Color.CYAN}  ╔══════════════════════════════════════════════════════════════════╗")
    print(f"  ║   AGENTIC AI WORKFLOW SUMMARY                                    ║")
    print(f"  ╠══════════════════════════════════════════════════════════════════╣")
    print(f"  ║   Total Time: 5 minutes 23 seconds                               ║")
    print(f"  ║   Workers Executed: 5 (Consent → KYC → Amount → Docs → Decision)║")
    print(f"  ║   State Transitions: 7                                           ║")
    print(f"  ║   LLM API Calls: 12                                              ║")
    print(f"  ║   Database Writes: 15 (audit trail)                              ║")
    print(f"  ║   OCR Documents: 3 (avg confidence: 98%)                         ║")
    print(f"  ║   Decision: APPROVED (explainable)                               ║")
    print(f"  ║   Compliance: RBI-compliant (100% auditable)                     ║")
    print(f"  ╚══════════════════════════════════════════════════════════════════╝{Color.END}\n")
    
    print(f"{Color.GREEN}{Color.BOLD}  ✓ Loan origination complete - Customer can now e-sign{Color.END}\n")

def main():
    """Run complete demonstration"""
    print_header()
    time.sleep(1)
    
    print(f"{Color.WHITE}{Color.BOLD}\n  Starting TIA-Sales Agentic AI Demonstration...\n{Color.END}")
    time.sleep(1)
    
    # Simulate user interaction
    user_message = "I need a personal loan of 5 lakhs"
    session_id = "sess_20251217_103045"
    
    # Layer 1: Input Guardrails
    simulate_input_guardrails(user_message)
    
    # Layer 2: Semantic Router
    simulate_semantic_router(user_message)
    
    # Layer 3: Context Manager
    simulate_context_manager(session_id)
    
    # Layer 4: Master Agent
    simulate_master_agent()
    
    # Layer 5: Worker Agents
    simulate_consent_worker()
    simulate_kyc_worker()
    simulate_amount_worker()
    simulate_document_worker()
    simulate_underwriting_worker()
    simulate_decision_worker()
    
    # Final Summary
    simulate_final_summary()
    
    print(f"\n{Color.BLUE}{'='*75}")
    print(f"  Demo complete. Press Ctrl+C to exit.{Color.END}")
    print(f"{Color.BLUE}{'='*75}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Color.YELLOW}  Demo interrupted. Thank you!{Color.END}\n")
        sys.exit(0)
