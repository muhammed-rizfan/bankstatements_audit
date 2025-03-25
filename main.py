import os
from transaction_grouper import TransactionGrouper

def main():
    # Detect which PDF to process
    if os.path.exists('SBI.pdf'):
        input_file = 'SBI.pdf'
    elif os.path.exists('hdfc bank.pdf'):
        input_file = 'hdfc bank.pdf'
    else:
        print("No bank statement PDF found. Please ensure SBI.pdf or hdfc bank.pdf exists.")
        return
        
    grouper = TransactionGrouper(input_file)
    output_file = f"categorized_transactions_{grouper.bank_type.lower()}.csv"
    df = grouper.export_to_csv(output_file)
    
    print(f"\nProcessed {len(df)} transactions from {grouper.bank_type} bank statement")
    print(f"Results exported to '{output_file}'")

if __name__ == "__main__":
    main()
