import re
from typing import List, Dict, Tuple, Callable
from extractors.base_extractor import BaseExtractor

class HDFCExtractor(BaseExtractor):
    """Extractor for HDFC bank statements"""
    
    def extract_transaction_details(self, description: str, ref_no: str) -> Tuple[str, str]:
        """HDFC specific transaction patterns"""
        # Credit Card Payments
        if any(x in description.upper() for x in ["HDFC CREDIT", "HDFCBANK CREDIT", "CC PMT"]):
            return "CREDIT_CARD_PAYMENT", "HDFC_CREDIT_CARD"
            
        # Loan EMI
        if any(x in description.upper() for x in ["EMI", "LOAN PMT", "HDFC LOAN"]):
            loan_type = "PERSONAL_LOAN"
            if "HOME" in description.upper():
                loan_type = "HOME_LOAN"
            elif "AUTO" in description.upper() or "CAR" in description.upper():
                loan_type = "AUTO_LOAN"
            return "LOAN_EMI", loan_type

        # ATM Withdrawals
        atm_patterns = ["ATM/", "ATM WDL", "CASH WDL", "ATM CASH"]
        if any(x in description.upper() for x in atm_patterns):
            location_match = re.search(r'ATM/(?:WDL/)?([^/]+)', description)
            location = location_match.group(1) if location_match else "ATM"
            return "ATM_WITHDRAWAL", location

        # NEFT/RTGS Transfers
        if any(x in description.upper() for x in ["NEFT", "RTGS"]):
            # Try to extract beneficiary name
            name_match = re.search(r'(?:NEFT|RTGS)[^a-zA-Z]*([A-Za-z\s]+)', description)
            beneficiary = name_match.group(1).strip() if name_match else "BANK_TRANSFER"
            return "BANK_TRANSFER_NEFT_RTGS", beneficiary

        # IMPS Transfers
        if "IMPS" in description.upper():
            name_match = re.search(r'IMPS[^a-zA-Z]*([A-Za-z\s]+)', description)
            beneficiary = name_match.group(1).strip() if name_match else "IMPS_TRANSFER"
            return "BANK_TRANSFER_IMPS", beneficiary
            
        # Cash Deposits including CDM
        if any(x in description for x in ["CASH DEPOSIT", "CSH DEP", "CDM"]):
            if "CDM" in description:
                # Extract location after CDM number
                cdm_match = re.search(r'CDM\d+([^-]+)', description)
                if cdm_match:
                    location = cdm_match.group(1).strip()
                    return "CASH_DEPOSIT_CDM", location
            else:
                location = description.split("at")[-1].strip() if "at" in description else "BRANCH"
                return "CASH_DEPOSIT", f"CASH-{location}"
                
        return "UNCATEGORIZED", "UNKNOWN"
        
    def extract_transactions(self, text: str, detail_extractor: Callable) -> List[Dict]:
        """Extract transactions from HDFC bank statement text"""
        transactions = []
        
        # Save raw text for debugging
        import os
        from pathlib import Path
        raw_text_path = f"{Path('HDFC')}_raw_text.txt"
        with open(raw_text_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Raw text saved to {raw_text_path} for debugging")
        
        # Split text into lines
        lines = text.split('\n')
        
        # Define patterns for HDFC bank statement transactions
        date_patterns = [
            r'(\d{2}/\d{2}/\d{2,4})',  # DD/MM/YY or DD/MM/YYYY
            r'(\d{2}-\d{2}-\d{2,4})',  # DD-MM-YY or DD-MM-YYYY
            r'(\d{2}\s+[A-Za-z]{3}\s+\d{2,4})'  # DD MMM YYYY
        ]
        
        # Process each line
        for i, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                continue
            
            # Look for date pattern
            date_found = False
            date = None
            
            for pattern in date_patterns:
                date_match = re.search(pattern, line)
                if date_match:
                    date = date_match.group(1)
                    date_found = True
                    break
            
            if date_found:
                # Extract amounts
                amount_pattern = r'(\d{1,3}(?:,\d{3})*\.\d{2})'
                amounts = re.findall(amount_pattern, line)
                
                if amounts:
                    # Extract description - anything between date and first amount
                    date_pos = line.find(date) + len(date)
                    first_amount_pos = line.find(amounts[0], date_pos)
                    
                    if first_amount_pos > date_pos:
                        description = line[date_pos:first_amount_pos].strip()
                        
                        # Default values
                        debit = 0.0
                        credit = 0.0
                        balance = 0.0
                        
                        # Determine if debit or credit based on context
                        if len(amounts) == 1:
                            balance = float(amounts[0].replace(',', ''))
                        elif len(amounts) == 2:
                            # Check for credit indicators
                            if "Cr" in line or "CR" in line:
                                credit = float(amounts[0].replace(',', ''))
                            else:
                                debit = float(amounts[0].replace(',', ''))
                            balance = float(amounts[-1].replace(',', ''))
                        elif len(amounts) >= 3:
                            # Try to determine which is which
                            if "Dr" in line or "DR" in line:
                                debit = float(amounts[0].replace(',', ''))
                                balance = float(amounts[-1].replace(',', ''))
                            elif "Cr" in line or "CR" in line:
                                credit = float(amounts[0].replace(',', ''))
                                balance = float(amounts[-1].replace(',', ''))
                            else:
                                # Just use the amounts in order
                                debit = float(amounts[0].replace(',', ''))
                                credit = float(amounts[1].replace(',', ''))
                                balance = float(amounts[-1].replace(',', ''))
                        
                        # Extract transaction type and party
                        txn_type, party = detail_extractor(description, "")
                        
                        transactions.append({
                            'date': date,
                            'description': description,
                            'reference_no': '',
                            'debit': debit,
                            'credit': credit,
                            'balance': balance,
                            'transaction_type': txn_type,
                            'party': party
                        })
        
        return transactions 