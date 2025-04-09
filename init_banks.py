import json
import os
from app import app, db
from models import Bank

def init_banks(start_index=0, batch_size=50):
    """
    Initialize Nigerian banks in the database from the provided JSON data.
    
    This will:
    1. Read the bank data from the JSON file
    2. Add banks in batches (50 at a time by default)
    3. Start from the specified index
    
    Args:
        start_index: The index to start from in the bank_data list
        batch_size: Number of banks to add in this batch
        
    Returns:
        Tuple of (success, message)
    """
    try:
        with open('bank_codes.json', 'r') as f:
            banks_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading bank data: {e}")
        return False, f"Error loading bank data: {e}"
    
    # Convert dictionary to list of (name, code) tuples for easier batch processing
    banks_list = [(bank_name, bank_code) for bank_name, bank_code in banks_data.items()]
    total_banks = len(banks_list)
    
    # Validate start index
    if start_index < 0 or start_index >= total_banks:
        message = f"Invalid start_index: {start_index}. Must be between 0 and {total_banks-1}"
        print(message)
        return False, message
    
    # Calculate end index
    end_index = min(start_index + batch_size, total_banks)
    
    # Counter for added banks
    added_count = 0
    
    # Process banks in the current batch
    for i in range(start_index, end_index):
        bank_name, bank_code = banks_list[i]
        
        # Check if bank already exists
        if not Bank.query.filter((Bank.name == bank_name) | (Bank.bank_code == bank_code)).first():
            bank = Bank(
                name=bank_name,
                bank_code=bank_code
            )
            db.session.add(bank)
            added_count += 1
    
    # Commit changes if any banks were added
    if added_count > 0:
        db.session.commit()
        print(f"Added {added_count} new banks to the database.")
    else:
        print("No new banks added in this batch.")
    
    # Report progress and status
    progress_msg = f"Processed banks {start_index+1}-{end_index} of {total_banks}"
    if end_index >= total_banks:
        progress_msg += " (COMPLETE)"
    else:
        progress_msg += f" (Next batch starts at index {end_index})"
        
    result_msg = f"{progress_msg}. Added {added_count} new banks to the database."
    
    return True, result_msg

def create_bank_json():
    """Create a JSON file of bank codes from the provided raw text."""
    try:
        with open('attached_assets/Pasted--9-payment-service-Bank-120001-AB-MICROFINANCE-BANK-090270-ABBEY-MORTGAGE--1744236153360.txt', 'r') as f:
            raw_data = f.read()
    except FileNotFoundError as e:
        print(f"Error reading file: {e}")
        return False, f"Error reading file: {e}"
    
    # Convert the raw text to a JSON object
    bank_data = {}
    
    # Each line is in format: "BANK NAME": "CODE",
    for line in raw_data.strip().splitlines():
        line = line.strip()
        if not line or not ('"' in line or "'" in line):
            continue
            
        try:
            # Split by first colon and remove quotes, spaces, and commas
            parts = line.split(':', 1)
            if len(parts) != 2:
                continue
                
            bank_name = parts[0].strip().strip('"').strip("'").strip()
            bank_code = parts[1].strip().strip('"').strip("'").strip(',').strip()
            
            if bank_name and bank_code:
                bank_data[bank_name] = bank_code
        except Exception as e:
            print(f"Error parsing line '{line}': {e}")
    
    # Write to a new JSON file
    with open('bank_codes.json', 'w') as f:
        json.dump(bank_data, f, indent=4)
    
    print(f"Created bank_codes.json with {len(bank_data)} banks.")
    return True, f"Created bank_codes.json with {len(bank_data)} banks."

def create_or_update_banks():
    """Create JSON file or initialize banks based on command line arguments."""
    import sys
    
    with app.app_context():
        if len(sys.argv) > 1:
            # Parse command line arguments
            if sys.argv[1] == 'create_json':
                # Just create the JSON file
                success, message = create_bank_json()
                print(message)
            elif sys.argv[1] == 'batch':
                # Process a specific batch
                start_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
                batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else 50
                success, message = init_banks(start_index, batch_size)
                print(message)
            elif sys.argv[1] == 'count':
                # Report the number of banks in the database
                bank_count = Bank.query.count()
                total_banks = 0
                try:
                    with open('bank_codes.json', 'r') as f:
                        banks_data = json.load(f)
                    total_banks = len(banks_data)
                except Exception as e:
                    print(f"Error reading bank_codes.json: {e}")
                
                print(f"Database has {bank_count} banks out of {total_banks} in the JSON file.")
            else:
                # Default operation
                success, message = init_banks()
                print(message)
        else:
            # Default operation (process first batch)
            success, message = init_banks()
            print(message)

if __name__ == "__main__":
    create_or_update_banks()