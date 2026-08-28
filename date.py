from app import create_app, db
from app.models import Expense

app = create_app()  # Initialize Flask app

with app.app_context():  # Ensure we are inside the Flask application context
    expenses = Expense.query.all()
    for exp in expenses:
        print(exp.date, exp.category, exp.amount, exp.description)
