import json
import os
from app import app, db
from models import Bank

def init_banks():
    """
    Initialize Nigerian banks in the database from the provided JSON data.
    
    This will:
    1. Read the bank data from the JSON file
    2. Add each bank to the database if it doesn't already exist
    """
    try:
        with open('bank_codes.json', 'r') as f:
            banks_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading bank data: {e}")
        return False, f"Error loading bank data: {e}"
    
    # Counter for added banks
    added_count = 0
    
    # Process each bank
    for bank_name, bank_code in banks_data.items():
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
        print("No new banks added to the database.")
    
    return True, f"Processed bank data. Added {added_count} new banks."

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

if __name__ == "__main__":
    with app.app_context():
        # First create the JSON file
        success, message = create_bank_json()
        if success:
            # Then initialize the banks
            init_banks()