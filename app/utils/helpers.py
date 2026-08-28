from datetime import datetime
import re
import logging
from app import db
from app.models import Expense

# Set up logging for debugging purposes
logging.basicConfig(level=logging.DEBUG)

def format_currency(amount):
    """Format a number as currency."""
    return f"₹{amount:,.2f}"

def parse_date(date_string):
    """
    Parse a date string in the format 'YYYY-MM-DD', 'MM/DD/YYYY', 'DD-MM-YYYY', or 'DD/MM/YYYY'.
    Returns a datetime object.
    """
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%d/%m/%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            continue
    return None  # Return None if no valid date format is found

def calculate_totals(expenses):
    """
    Calculate total expenses by category.
    Args:
        expenses (list): A list of dictionaries or objects with 'category' and 'amount' keys.
    Returns:
        dict: A dictionary with categories as keys and total amounts as values.
    """
    totals = {}
    for expense in expenses:
        category = expense.get('category') or expense.category
        amount = expense.get('amount') or expense.amount
        totals[category] = totals.get(category, 0) + amount
    return totals

def validate_file_extension(filename, allowed_extensions=("jpg", "png", "jpeg")):
    """
    Validate if a file has an allowed extension.
    Args:
        filename (str): The name of the file to validate.
        allowed_extensions (tuple): Tuple of allowed extensions (default: ("jpg", "png", "jpeg")).
    Returns:
        bool: True if the file is valid, False otherwise.
    """
    if not "." in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in allowed_extensions

def parse_receipt_text(text):
    """
    Extracts date, amount, category, and description from receipt text.
    Returns (date, amount, category, description).
    """
    logging.debug(f"Extracted text: {text}")  # Log the extracted text for debugging
    
    lines = text.split('\n')
    amount = None
    category = 'Other'  # Default category
    description = 'Receipt Expense'
    extracted_date = None
    possible_amounts = []

    # Category mapping based on common keywords
    category_mapping = {
        "food": "Food", "restaurant": "Food", "dining": "Food",
        "transport": "Transport", "taxi": "Transport", "bus": "Transport",
        "bill": "Bills", "electricity": "Bills", "water": "Bills",
        "entertainment": "Entertainment", "movie": "Entertainment",
        "shopping": "Shopping", "clothing": "Shopping",
        "grocery": "Food", "supermarket": "Food",
        "hotel": "Food", "stay": "Other", "biryani": "Food", "pulao": "Food",
        "soft drinks": "Food"
    }

    for line in lines:
        clean_line = line.strip().lower()

        # Extract date (formats like YYYY-MM-DD, MM/DD/YYYY, DD-MM-YYYY, DD/MM/YYYY)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}|\d{2}/\d{2}/\d{2})', line)
        if date_match:
            extracted_date = parse_date(date_match.group(1))
            logging.debug(f"Found date: {extracted_date}")

        # Extract all possible amounts (including ₹ or currency signs)
        matches = re.findall(r'₹?\s?(\d{1,3}(?:,\d{3})*\.\d{2})', line)
        for match in matches:
            try:
                possible_amounts.append(float(match.replace(',', '').strip()))
            except ValueError:
                continue  # Skip if conversion fails

        # Identify category based on keywords
        for keyword, cat in category_mapping.items():
            if keyword in clean_line:
                category = cat
                break

        # Extract business/store name from the top lines of the receipt
        if description == 'Receipt Expense' and len(clean_line) > 3 and not any(char.isdigit() for char in clean_line):
            description = line.strip()

    # Pick the highest amount (assumes total is the largest)
    if possible_amounts:
        amount = max(possible_amounts)
        logging.debug(f"Extracted amounts: {possible_amounts}, Selected: ₹{amount}")

    # If no date was extracted, use today's date
    if extracted_date is None:
        extracted_date = datetime.today().date()
        logging.debug(f"No date found, using today's date: {extracted_date}")

    # Ensure category is set to 'Food' if a restaurant name is found
    if "restaurant" in description.lower() or "hotel" in description.lower():
        category = "Food"

    # Final check if amount wasn't extracted
    if amount is None:
        logging.warning("No amount extracted from receipt text.")
        amount = 0.0  # Set default to 0 if no amount found

    return extracted_date, amount, category, description

def save_expense(data, user_id):
    try:
        print(f"🔹 Received Data: {data}, User ID: {user_id}")  

        expense = Expense(
            user_id=user_id,
            date=data["date"],  # Make sure 'date' is in correct format (YYYY-MM-DD)
            category=data["category"],
            amount=data["amount"],
            description=data["description"]
        )

        db.session.add(expense)
        db.session.commit()

        print(f"✅ Expense saved: {expense.id}, {expense.amount}, {expense.category}")
        return expense  # Make sure we return the saved expense

    except Exception as e:
        print(f"❌ ERROR saving expense: {e}")
        db.session.rollback()
        return None
    db.session.add(expense)
    db.session.commit()
