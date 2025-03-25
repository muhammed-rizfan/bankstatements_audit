# # import tabula
# # import pandas as pd
# # import warnings

# # # Suppress specific warnings
# # warnings.filterwarnings("ignore", category=UserWarning, module="pdfbox")

# # def pdf_to_csv(pdf_path, csv_path):
# #     """Convert a PDF file to a CSV file using tabula-py."""
# #     try:
# #         # Read tables from PDF
# #         tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
        
# #         # Combine all tables into a single DataFrame
# #         df = pd.concat(tables, ignore_index=True)
        
# #         # Save the DataFrame to a CSV file
# #         df.to_csv(csv_path, index=False)
# #         print(f"PDF data has been converted and saved to {csv_path}")
# #     except Exception as e:
# #         print(f"An error occurred: {e}")

# # # Example usage
# # pdf_path = 'SBI.pdf'  # Path to your PDF file
# # csv_path = 'output.csv'       # Path to save the CSV file
# # pdf_to_csv(pdf_path, csv_path)



# import pandas as pd
# import re
# from datetime import datetime

# def clean_amount(amount_str):
#     """Clean amount strings by removing commas and converting to float"""
#     if isinstance(amount_str, str):
#         return float(amount_str.replace(',', ''))
#     return amount_str

# def parse_bank_statement(text_content):
#     """Parse bank statement text content into structured data"""
    
#     # Extract account details
#     account_info = {
#         'Account_Name': re.search(r': (Mr\. .+)', text_content).group(1),
#         'Account_Number': re.search(r': (\d{19})', text_content).group(1),
#         'Branch': re.search(r'Branch\s+: (.+)', text_content).group(1),
#         'Statement_Period': 'from 1 Apr 2023 to 31 Mar 2024'
#     }
    
#     # Find all transaction rows using regex
#     transactions = []
    
#     # Split content into lines
#     lines = text_content.split('\n')
    
#     for line in lines:
#         # Look for lines that start with a date pattern
#         date_pattern = r'(\d{1,2}\s*(?:Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Jan|Feb|Mar)\s*2023)'
#         match = re.search(date_pattern, line)
        
#         if match:
#             # Extract transaction details
#             # Split the line by multiple spaces to separate fields
#             fields = [f for f in re.split(r'\s{2,}', line) if f]
            
#             if len(fields) >= 4:  # Ensure we have enough fields
#                 try:
#                     date = fields[0]
#                     description = ' '.join([f for f in fields[1:-3] if f])  # Join middle fields for description
#                     ref_no = fields[-3] if not fields[-3].replace('.', '').isdigit() else ''
                    
#                     # Get debit/credit/balance amounts
#                     amounts = [f for f in fields[-3:] if f.replace(',', '').replace('.', '').isdigit()]
                    
#                     if len(amounts) >= 2:
#                         debit = amounts[-2] if len(amounts) > 2 else '0'
#                         balance = amounts[-1]
                        
#                         transactions.append({
#                             'Date': date,
#                             'Description': description,
#                             'Reference_No': ref_no,
#                             'Debit': clean_amount(debit),
#                             'Balance': clean_amount(balance)
#                         })
#                 except Exception as e:
#                     print(f"Error processing line: {line}")
#                     print(f"Error: {str(e)}")
#                     continue
    
#     # Create DataFrame
#     df = pd.DataFrame(transactions)
    
#     # Add account info as metadata columns
#     for key, value in account_info.items():
#         df[key] = value
    
#     # Reorder columns
#     column_order = ['Date', 'Description', 'Reference_No', 'Debit', 'Balance', 
#                    'Account_Name', 'Account_Number', 'Branch', 'Statement_Period']
#     df = df[column_order]
    
#     return df

# def save_to_csv(df, output_file='bank_statement_1.csv'):
#     """Save DataFrame to CSV file"""
#     df.to_csv(output_file, index=False)
#     print(f"CSV file has been created: {output_file}")

# # Main execution
# def main(text_content):
#     # Parse the statement
#     df = parse_bank_statement(text_content)
    
#     # Save to CSV
#     save_to_csv(df)
    
#     # Print summary
#     print("\nStatement Summary:")
#     print(f"Total Transactions: {len(df)}")
#     print(f"Date Range: {df['Date'].iloc[0]} to {df['Date'].iloc[-1]}")
#     print(f"Opening Balance: {df['Balance'].iloc[0]}")
#     print(f"Closing Balance: {df['Balance'].iloc[-1]}")
    
#     return df

# # Usage example:
# if __name__ == "__main__":
#     # The text_content would be the PDF text content
#     # main(text_content)
#     pass






# import pandas as pd
# import re
# from datetime import datetime

# def extract_metadata(text_content):
#     """Extract account metadata from the statement"""
#     metadata = {}
#     try:
#         metadata['Account_Name'] = re.search(r'Account Name\s*:\s*([^\n]+)', text_content).group(1).strip()
#         metadata['Account_Number'] = re.search(r'Account\s+Number\s*:\s*(\d+)', text_content).group(1).strip()
#         metadata['Branch'] = re.search(r'Branch\s*:\s*([^\n]+)', text_content).group(1).strip()
#         metadata['Opening_Balance'] = float(re.search(r'Balance as on 1 Apr 2023\s*:\s*([\d,\.]+)', text_content).group(1).replace(',', ''))
#     except AttributeError:
#         print("Warning: Some metadata fields could not be extracted")
#     return metadata

# def parse_amount(amount_str):
#     """Parse amount string to float"""
#     if not amount_str:
#         return 0.0
#     return float(amount_str.replace(',', ''))

# def parse_transactions(text_content):
#     """Parse transaction records from the statement"""
#     transactions = []
    
#     # Split into lines and clean
#     lines = [line.strip() for line in text_content.split('\n') if line.strip()]
    
#     # Regular expressions for parsing
#     date_pattern = r'(\d{1,2}\s+(?:Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Jan|Feb|Mar)\s+2023)'
#     amount_pattern = r'([\d,]+\.\d{2})'
    
#     for line in lines:
#         # Check if line contains a transaction
#         if re.match(date_pattern, line):
#             try:
#                 # Split line into components
#                 parts = [p.strip() for p in re.split(r'\s{2,}', line) if p.strip()]
                
#                 # Extract date
#                 date = parts[0]
                
#                 # Find amounts at the end of the line
#                 amounts = []
#                 while parts and re.match(amount_pattern, parts[-1]):
#                     amounts.insert(0, parts.pop())
                
#                 # Extract reference number and description
#                 ref_no = ''
#                 if len(parts) > 1:
#                     description = ' '.join(parts[1:])
#                     # Try to extract reference number from description
#                     ref_match = re.search(r'([A-Z0-9]{10,})', description)
#                     if ref_match:
#                         ref_no = ref_match.group(1)
#                 else:
#                     description = ''
                
#                 # Parse amounts
#                 if len(amounts) >= 2:
#                     debit = parse_amount(amounts[-2])
#                     balance = parse_amount(amounts[-1])
                    
#                     transactions.append({
#                         'Date': date,
#                         'Description': description,
#                         'Reference_No': ref_no,
#                         'Debit': debit,
#                         'Balance': balance
#                     })
#             except Exception as e:
#                 print(f"Error parsing line: {line}")
#                 print(f"Error details: {str(e)}")
#                 continue
    
#     return transactions

# def process_bank_statement(text_content):
#     """Process the complete bank statement"""
#     # Extract metadata
#     metadata = extract_metadata(text_content)
    
#     # Parse transactions
#     transactions = parse_transactions(text_content)
    
#     # Create DataFrame
#     df = pd.DataFrame(transactions)
    
#     # Add metadata columns
#     for key, value in metadata.items():
#         df[key] = value
    
#     # Reorder columns
#     column_order = ['Date', 'Description', 'Reference_No', 'Debit', 'Balance',
#                    'Account_Name', 'Account_Number', 'Branch']
#     df = df[[col for col in column_order if col in df.columns]]
    
#     return df

# def save_to_csv(df, output_file='bank_statement_processed.csv'):
#     """Save the processed data to CSV"""
#     df.to_csv(output_file, index=False)
#     print(f"\nProcessed data saved to: {output_file}")
#     print(f"Total transactions: {len(df)}")
#     print(f"Date range: {df['Date'].iloc[0]} to {df['Date'].iloc[-1]}")
#     print(f"Opening balance: {df['Balance'].iloc[0]}")
#     print(f"Closing balance: {df['Balance'].iloc[-1]}")

# # Main execution function
# def main():
#     try:
#         # Read the PDF content
#         with open('monthly_profits.csv', 'r', encoding='utf-8') as file:
#             text_content = file.read()
        
#         # Process the statement
#         df = process_bank_statement(text_content)
        
#         # Save to CSV
#         save_to_csv(df)
        
#         return df
#     except Exception as e:
#         print(f"Error processing statement: {str(e)}")
#         return None

# if __name__ == "__main__":
#     df = main()



import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import pandas as pd
import re
import os

def pdf_to_images(pdf_path):
    """Convert PDF pages to images."""
    try:
        doc = fitz.open(pdf_path)
        images = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(alpha=False)
            # Convert pixmap to PIL Image
            img_bytes = pix.tobytes()
            img = Image.frombytes("RGB", [pix.width, pix.height], img_bytes)
            images.append(img)
        doc.close()
        return images
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        return []

def ocr_images_to_text(images):
    """Perform OCR on images to extract text."""
    all_text = []
    for i, img in enumerate(images):
        print(f"Processing page {i+1}/{len(images)}...")
        text = pytesseract.image_to_string(img, config='--psm 6')
        all_text.append(text)
    return all_text

def extract_transactions_from_text(text_data):
    """Extract transaction data from OCR text."""
    transactions = []
    
    # Join all pages
    full_text = "\n".join(text_data)
    
    # Look for transaction patterns in HDFC statements
    # This pattern may need adjustment based on the actual format
    transaction_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+([^\n]+?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})\s+(\d{1,3}(?:,\d{3})*\.\d{2})'
    
    matches = re.finditer(transaction_pattern, full_text)
    
    for match in matches:
        date, description, amount, balance = match.groups()
        
        # Determine if debit or credit based on context
        # This is a simplification - you may need to adjust based on your statement format
        debit = 0.0
        credit = 0.0
        
        # Clean amount (remove commas)
        amount_clean = float(amount.replace(',', ''))
        
        # Assume it's a debit by default (you'll need to adjust this logic)
        debit = amount_clean
        
        transactions.append({
            'date': date,
            'description': description.strip(),
            'reference_no': '',  # May need to extract from description
            'debit': debit,
            'credit': credit,
            'balance': float(balance.replace(',', ''))
        })
    
    return transactions

def pdf_to_csv(pdf_path, csv_path):
    """Convert a PDF to CSV using OCR."""
    try:
        # Convert PDF to images
        images = pdf_to_images(pdf_path)
        if not images:
            print("No images extracted from PDF")
            return False
            
        # Extract text using OCR
        text_data = ocr_images_to_text(images)
        
        # Extract transactions from text
        transactions = extract_transactions_from_text(text_data)
        
        if not transactions:
            print("No transactions found in the text")
            # Save the raw text for debugging
            with open(f"{os.path.splitext(csv_path)[0]}_raw_text.txt", 'w', encoding='utf-8') as f:
                f.write("\n\n===PAGE BREAK===\n\n".join(text_data))
            print(f"Raw text saved to {os.path.splitext(csv_path)[0]}_raw_text.txt for debugging")
            return False
        
        # Convert to DataFrame and save as CSV
        df = pd.DataFrame(transactions)
        df.to_csv(csv_path, index=False)
        print(f"Successfully extracted {len(transactions)} transactions to {csv_path}")
        return True
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    pdf_path = "hdfc bank.pdf"  # Replace with your PDF file path
    csv_path = "hdfc_transactions.csv"  # Replace with your desired CSV file path
    pdf_to_csv(pdf_path, csv_path)
    print(f"Process completed. Check {csv_path} for results.")