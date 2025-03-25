import re
from typing import List, Dict, Tuple, Callable
from extractors.base_extractor import BaseExtractor

class SBIExtractor(BaseExtractor):
    """Extractor for SBI bank statements"""
    
    def extract_transaction_details(self, description: str, ref_no: str) -> Tuple[str, str]:
        """SBI specific transaction patterns"""
        # BY TRANSFER pattern
        if "BY TRANSFER" in description or "BY TRANSFER-" in description:
            # Extract beneficiary name
            transfer_match = re.search(r'BY TRANSFER-([^-]+)', description)
            beneficiary = transfer_match.group(1).strip() if transfer_match else "TRANSFER"
            return "BANK_TRANSFER", beneficiary

        # TO TRANSFER pattern
        if "TO TRANSFER" in description or "TO TRANSFER-" in description:
            # Extract beneficiary name
            transfer_match = re.search(r'TO TRANSFER-([^-]+)', description)
            beneficiary = transfer_match.group(1).strip() if transfer_match else "TRANSFER"
            return "BANK_TRANSFER", beneficiary

        # ATM withdrawals
        if "ATM CASH" in description or "ATM WDL" in description or "CASH WITHDRAWAL" in description:
            location_match = re.search(r'ATM\s+([A-Za-z0-9\s]+)', description)
            location = location_match.group(1).strip() if location_match else "ATM"
            return "ATM_WITHDRAWAL", f"ATM-{location}"

        # Internet Banking
        if "INB" in description or "INTERNET BANKING" in description:
            return "INTERNET_BANKING", "SBI_INTERNET_BANKING"

        # Cheque deposits/withdrawals
        if "CHEQUE" in description or "CHQ" in description:
            cheque_num = re.search(r'(?:CHEQUE|CHQ)[^\d]*(\d+)', description)
            cheque_id = cheque_num.group(1) if cheque_num else "CHEQUE"
            return "CHEQUE_TRANSACTION", f"CHEQUE-{cheque_id}"
            
        # BULK POSTING (common in SBI)
        if "BULK POSTING" in description:
            parts = description.split('-')
            if len(parts) > 1:
                merchant = parts[-2].strip() if len(parts) > 2 else parts[-1].strip()
                merchant = re.sub(r'\d+', '', merchant).strip()
                return "MERCHANT_PAYMENT", merchant
                
        # Cash Deposits
        if "CASH DEPOSIT" in description:
            location = description.split("at")[-1].strip() if "at" in description else "BRANCH"
            return "CASH_DEPOSIT", f"CASH-{location}"
            
        # Insurance premiums
        if any(x in description for x in ["PMJJBY", "PMSBY"]):
            return "INSURANCE_PREMIUM", "INSURANCE_PREMIUM"
            
        return "UNCATEGORIZED", "UNKNOWN"
        
    def extract_transactions(self, text: str, detail_extractor: Callable) -> List[Dict]:
        """Extract transactions from SBI bank statement text"""
        transactions = []
        
        # Save raw text for debugging
        import os
        from pathlib import Path
        raw_text_path = f"{Path('SBI')}_raw_text.txt"
        with open(raw_text_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Raw text saved to {raw_text_path} for debugging")
        
        # Split text into lines
        lines = text.split('\n')
        
        # Define patterns for bank statement transactions
        date_patterns = [
            r'(\d{2}/\d{2}/\d{2,4})',  # DD/MM/YY or DD/MM/YYYY
            r'(\d{2}-\d{2}-\d{2,4})',  # DD-MM-YY or DD-MM-YYYY
            r'(\d{2}\s+[A-Za-z]{3}\s+\d{2,4})'  # DD MMM YYYY (SBI format)
        ]
        
        # SBI specific transaction marker
        sbi_transaction_start = False
        
        # Process each line
        for i, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                continue
            
            # Check for SBI transaction table headers
            if "Date" in line and "Description" in line and "Debit" in line and "Credit" in line and "Balance" in line:
                sbi_transaction_start = True
                continue
            
            if not sbi_transaction_start:
                continue
            
            # Look for date at the beginning of the line
            date_found = False
            date = None
            
            for pattern in date_patterns:
                date_match = re.search(pattern, line.strip())
                if date_match:
                    date = date_match.group(1)
                    date_found = True
                    break
            
            if date_found:
                # For SBI, try to extract all components
                # Split by multiple spaces to separate fields
                parts = [p for p in re.split(r'\s{2,}', line.strip()) if p.strip()]
                
                if len(parts) >= 3:  # At minimum we need date, description, and one amount
                    # Extract description - typically the second field
                    description = parts[1] if len(parts) > 1 else ""
                    
                    # Try to find amounts (debit, credit, balance)
                    amount_pattern = r'(\d{1,3}(?:,\d{3})*\.\d{2})'
                    amounts = re.findall(amount_pattern, line)
                    
                    if amounts:
                        # For SBI, determine debit/credit based on position
                        debit = 0.0
                        credit = 0.0
                        balance = 0.0
                        
                        # Check if we have enough fields to determine positions
                        if len(parts) >= 4:
                            # Try to identify which columns are which
                            for part in parts:
                                # Skip the date and description parts
                                if part == date or part == description:
                                    continue
                                    
                                # Check if this part contains an amount
                                amount_in_part = re.search(amount_pattern, part)
                                if amount_in_part:
                                    amount_str = amount_in_part.group(1)
                                    amount_val = float(amount_str.replace(',', ''))
                                    
                                    # Determine if it's debit, credit, or balance
                                    if "Dr" in part or "DR" in part:
                                        debit = amount_val
                                    elif "Cr" in part or "CR" in part:
                                        credit = amount_val
                                    else:
                                        # Assume the last amount is balance
                                        balance = amount_val
                        else:
                            # Simplified approach if we can't determine positions
                            if len(amounts) == 1:
                                balance = float(amounts[0].replace(',', ''))
                            elif len(amounts) == 2:
                                # Assume first is debit/credit and second is balance
                                if "Cr" in line or "CR" in line:
                                    credit = float(amounts[0].replace(',', ''))
                                else:
                                    debit = float(amounts[0].replace(',', ''))
                                balance = float(amounts[1].replace(',', ''))
                            elif len(amounts) >= 3:
                                # Assume format is debit, credit, balance
                                debit = float(amounts[0].replace(',', '')) if amounts[0] != '0.00' else 0.0
                                credit = float(amounts[1].replace(',', '')) if amounts[1] != '0.00' else 0.0
                                balance = float(amounts[2].replace(',', ''))
                        
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
        
        # If no transactions found with the standard pattern, try a more flexible approach
        if not transactions:
            print("No transactions found with standard SBI pattern. Trying alternative approach...")
            
            # For SBI statements, look for lines with date patterns and amounts
            for i, line in enumerate(lines):
                if not line.strip():
                    continue
                    
                # Look for any date pattern in the line
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
                            
                            # Determine debit/credit/balance based on position and context
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
                                debit_pos = line.find(amounts[0])
                                credit_pos = line.find(amounts[1])
                                balance_pos = line.find(amounts[-1])
                                
                                # If positions make sense (left to right)
                                if debit_pos < credit_pos < balance_pos:
                                    debit = float(amounts[0].replace(',', ''))
                                    credit = float(amounts[1].replace(',', ''))
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