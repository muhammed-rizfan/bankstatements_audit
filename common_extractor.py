import re
from typing import Tuple

def extract_common_transaction_details(description: str, ref_no: str) -> Tuple[str, str]:
    """Common transaction patterns for all banks"""
    # Salary Credits
    if any(x in description.upper() for x in ["SALARY", "SAL", "PAYROLL"]):
        company_match = re.search(r'(?:SALARY|SAL|PAYROLL)[^a-zA-Z]*([A-Za-z\s]+)', description)
        company = company_match.group(1).strip() if company_match else "EMPLOYER"
        return "SALARY_CREDIT", company

    # GST/Tax Payments
    if any(x in description.upper() for x in ["GST", "TDS", "TAX PMT"]):
        return "TAX_PAYMENT", "GST_OR_TDS"

    # Mutual Fund Investments
    if any(x in description.upper() for x in ["MF", "MUTUAL FUND", "MFSS"]):
        fund_match = re.search(r'(?:MF|MUTUAL FUND|MFSS)[^a-zA-Z]*([A-Za-z\s]+)', description)
        fund = fund_match.group(1).strip() if fund_match else "MUTUAL_FUND"
        return "INVESTMENT_MF", fund

    # Standing Instructions/Auto-debits
    if any(x in description.upper() for x in ["SI-", "STANDING INSTR", "AUTO DEBIT"]):
        purpose_match = re.search(r'(?:SI-|STANDING INSTR|AUTO DEBIT)[^a-zA-Z]*([A-Za-z\s]+)', description)
        purpose = purpose_match.group(1).strip() if purpose_match else "STANDING_INSTRUCTION"
        return "STANDING_INSTRUCTION", purpose

    # SIP/Investment Transactions
    if "-SIP-" in description:
        fund_match = re.search(r'SIP-\d+-(.+?)(?:-|$)', description)
        if fund_match:
            fund_name = fund_match.group(1).strip()
            return "INVESTMENT_SIP", fund_name

    # Bill Payments
    bill_keywords = ["BILLDESK", "BILL PAYMENT", "AIRTELDTHD"]
    if any(keyword in description for keyword in bill_keywords):
        if "SBICARD" in description:
            return "CARD_PAYMENT", "SBICARD"
        elif "Airtel" in description:
            return "BILL_PAYMENT", "AIRTEL"
        else:
            merchant_match = re.search(r'(?:BILLDESK|BILL PAYMENT)\s*([A-Za-z\s]+)', description)
            merchant = merchant_match.group(1).strip() if merchant_match else "BILL_PAYMENT"
            return "BILL_PAYMENT", merchant

    # UPI Transactions
    upi_match = re.search(r'UPI/(?:DR|CR)/\d+/([^/]+)/\w+/', description)
    if upi_match:
        recipient = upi_match.group(1).strip()
        recipient = re.sub(r'\s*(?:Ltd|Limited|Pvt|Private|IND|INDIA)\s*$', '', recipient)
        return "UPI_TRANSFER", recipient

    # Insurance Premiums
    if any(x in description for x in ["INSURANCE"]):
        company = "INSURANCE_PREMIUM"
        if "ICICI" in description:
            company = "ICICI_INSURANCE"
        elif "SBI" in description:
            company = "SBI_INSURANCE"
        return "INSURANCE_PREMIUM", company

    # Check for specific merchants/services
    known_merchants = {
        "IRCTC": "TRAVEL",
        "Makemytrip": "TRAVEL",
        "NETFLIX": "SUBSCRIPTION",
        "Amazon": "SHOPPING",
        "Flipkart": "SHOPPING"
    }
    for merchant, category in known_merchants.items():
        if merchant.upper() in description.upper():
            return f"{category}_PAYMENT", merchant
        
    # Online Shopping
    if "ONLINE SHOPPING" in description:
        merchant = re.search(r'ONLINE SHOPPING (.+)', description)
        if merchant:
            merchant_name = merchant.group(1).strip()
            return "ONLINE_SHOPPING", merchant_name

    # Try to extract transfer beneficiary
    if "TRANSFER" in description:
        if "FROM" in ref_no:
            beneficiary = ref_no.split("FROM")[-1].strip()
            return "BANK_TRANSFER", beneficiary
        elif "TO" in ref_no:
            beneficiary = ref_no.split("TO")[-1].strip()
            return "BANK_TRANSFER", beneficiary

    # If nothing else matches, try to extract any meaningful name
    name_match = re.search(r'[A-Z\s]{3,}(?:IND(?:IA)?)?', description)
    if name_match:
        return "OTHER_TRANSFER", name_match.group(0).strip()
        
    return "UNCATEGORIZED", "UNKNOWN" 