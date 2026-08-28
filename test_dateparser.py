from app import create_app, db
from app.routes import save_expense
from app.models import User, Expense

# Initialize Flask app correctly using create_app()
app = create_app()

with app.app_context():
    # Ensure database tables exist
    db.create_all()

    # Check if user exists
    user_id = 1
    user = User.query.get(user_id)
    if not user:
        print(f"❌ User ID {user_id} not found. Creating test user...")
        test_user = User(id=user_id, username="TestUser", email="test@example.com")
        db.session.add(test_user)
        db.session.commit()

    # Test Expense Data 
    test_expense = {
        "date": "2025-03-30",
        "category": "Miscellaneous",
        "amount": "6",
        "description": "Annapurna."
    }

    print("🔄 Testing save_expense function...")
    result = save_expense(test_expense, user_id)

    if result:
        print("✅ Expense saved successfully!")
    else:
        print("❌ Failed to save expense!")

    # Verify by querying the database
    expenses = Expense.query.filter_by(user_id=user_id).all()
    print(f"📊 Expenses in DB: {len(expenses)}")
    for exp in expenses:
        print(f"📅 {exp.date} | 💰 {exp.amount} | 📄 {exp.description}")
