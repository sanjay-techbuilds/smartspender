from datetime import datetime
import dateparser

def parse_date(date_str):
    try:
        print(f"🔍 Raw date received: {date_str}")  

        # First, try strict YYYY-MM-DD format
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            print(f"📅 Parsed Date (Strict): {parsed_date}")
            return parsed_date
        except ValueError:
            pass  # If strict parsing fails, try dateparser

        # Use dateparser for flexible formats
        parsed_date = dateparser.parse(date_str, settings={'DATE_ORDER': 'YMD'})
        if parsed_date:
            parsed_date = parsed_date.date()
            print(f"📅 Parsed Date (Flexible): {parsed_date}")
            return parsed_date

        print(f"❌ Unable to parse date: {date_str}")
        return None
    except Exception as e:
        print(f"❌ Date parsing error: {e}")
        return None


# ✅ Test cases
test_dates = [
    "2025-03-30",
    "30 March 2025",
    "March 30, 2025",
    "30/03/2025",
    "30-03-2025",
    "next Monday",
    "yesterday",
    "today"
]

# Run tests
for date_str in test_dates:
    print(f"\n📝 Testing: {date_str}")
    result = parse_date(date_str)
    print(f"✅ Parsed Result: {result}")
