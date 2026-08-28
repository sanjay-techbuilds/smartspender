from tkinter import Canvas
from flask import Blueprint, render_template, request, jsonify, flash, redirect, session, url_for, current_app
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.helpers import parse_receipt_text
from app.models import User, Expense, db
import os
from datetime import datetime
from app.utils.ocr import perform_ocr
from flask import send_file, Response
from reportlab.lib import colors # type: ignore
from reportlab.lib.pagesizes import letter # type: ignore
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph # type: ignore
from reportlab.lib.styles import getSampleStyleSheet # type: ignore
import io
import csv


main = Blueprint('main', __name__)

# Index Route (Dashboard) with Search Support
@main.route('/', methods=['GET', 'POST'])
@login_required  
def index():
    search_query = request.args.get('search_query', '')  
    print(f"🔍 DEBUG: Search Query - {search_query}")

    if search_query:
        expenses = Expense.query.filter(
            (Expense.description.ilike(f'%{search_query}%')) |
            (Expense.date.like(f'%{search_query}%'))
        ).all()
    else:
        expenses = Expense.query.filter_by(user_id=current_user.id).all()

    print(f"📊 DEBUG: Retrieved {len(expenses)} expenses for user {current_user.id}")

    for exp in expenses:
        print(f"📝 Expense: {exp.date} | {exp.category} | {exp.amount} | {exp.description}")

    total_expenses = sum(exp.amount for exp in expenses)  
    print(f"💰 DEBUG: Total Expenses - {total_expenses}")

    return render_template(
        'index.html',
        expenses=expenses,
        total=total_expenses,
        search_query=search_query,
        username=current_user.username  
    )

# Registration Route
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']  

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('main.register'))  

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('main.register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful!', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:  # Prevent logged-in users from seeing the login page
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)  # Logs in the user
            session['user_id'] = user.id  # Set user_id in session
            flash('Login successful!', 'success')

            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))

        flash('Invalid username or password.', 'danger')

    return render_template('auth.html')


# Logout Route
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

# Add Expense Page Route (renders the manual expense entry page)
@main.route('/add_expense', methods=['GET'])
@login_required
def add_expense_page():
    return render_template('add_expense.html')

# Handle manual expense form submission
@main.route('/add_expense', methods=['POST'])
@login_required
def add_expense_manual():
    try:
        expense_name = request.form.get("expense_name", "").strip()
        amount_str = request.form.get("expense_amount", "").strip()
        category = request.form.get("expense_category", "").lower().strip()
        date_str = request.form.get("expense_date", "today").strip()

        # Validate amount
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Invalid amount. Please enter a valid number.", "danger")
            return redirect(url_for("main.add_expense_page"))

        # Validate date
        if date_str == "today":
            date = datetime.today()
        else:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                flash("Invalid date format. Use YYYY-MM-DD.", "danger")
                return redirect(url_for("main.add_expense_page"))

        # Validate category
        valid_categories = ['food', 'transportation', 'utilities', 'entertainment', 'other']
        if category not in valid_categories:
            flash("Invalid category. Choose from: Food, Transportation, Utilities, Entertainment, Other.", "danger")
            return redirect(url_for("main.add_expense_page"))

        # Save expense
        new_expense = Expense(
            user_id=current_user.id,
            date=date,
            category=category,
            amount=amount,
            description=expense_name
        )
        db.session.add(new_expense)
        db.session.commit()

        flash("Expense added successfully!", "success")
        return redirect(url_for("main.index"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("main.add_expense_page"))

# Delete Expense Route
@main.route('/delete_expense/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_expense(id):
    expense = Expense.query.get(id)
    if expense and expense.user_id == current_user.id:
        db.session.delete(expense)
        db.session.commit()
        flash('Expense deleted successfully!', 'success')
    else:
        flash('Expense not found or permission denied.', 'danger')

    return redirect(url_for('main.index'))

# Edit Expense Route
@main.route('/edit_expense/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    expense = Expense.query.get(id)
    
    if expense and expense.user_id == current_user.id:
        if request.method == 'POST':
            date_str = request.form['expense_date']
            amount = float(request.form['expense_amount'])
            category = request.form['expense_category']
            expense_name = request.form['expense_name']
            
            date = datetime.strptime(date_str, '%Y-%m-%d')
            
            expense.date = date
            expense.amount = amount
            expense.category = category
            expense.description = expense_name
            db.session.commit()
            flash('Expense updated successfully!', 'success')
            return redirect(url_for('main.index'))
        
        return render_template('edit_expense.html', expense=expense)
    else:
        flash('Expense not found or permission denied.', 'danger')
        return redirect(url_for('main.index'))
    
@main.route("/download-report/<report_type>")
@login_required
def download_report(report_type):
    user_id = current_user.id
    expenses = Expense.query.filter_by(user_id=user_id).all()

    if not expenses:
        return "No expenses available to download", 404

    if report_type == "pdf":
        return generate_pdf(expenses)
    elif report_type == "csv":
        return generate_csv(expenses)
    else:
        return "Invalid report type", 400


def generate_pdf(expenses):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title = Paragraph("<b>Expense Report</b>", styles["Title"])
    elements.append(title)

    # Define table headers
    data = [["Date", "Category", "Amount (₹)", "Description"]]
    
    # Add expense data
    for exp in expenses:
        data.append([exp.date.strftime('%Y-%m-%d'), exp.category, f"₹{exp.amount:.2f}", exp.description])

    # Create table
    table = Table(data, colWidths=[100, 100, 100, 200])

    # Table styling
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ])
    
    table.setStyle(style)
    elements.append(table)

    # Build the PDF
    doc.build(elements)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="expense_report.pdf", mimetype="application/pdf")


def generate_csv(expenses):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Date", "Category", "Amount", "Description"])

    for exp in expenses:
        writer.writerow([exp.date.strftime('%Y-%m-%d'), exp.category, exp.amount, exp.description])

    buffer.seek(0)
    return Response(buffer, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=expense_report.csv"})

@main.route("/api/expenses")
@login_required  # This will ensure the user must be logged in to access this route
def get_expenses():
    user_id = current_user.id  # current_user is automatically set by Flask-Login

    # Query the expenses for the logged-in user
    expenses = Expense.query.filter_by(user_id=user_id).all()

    # If no expenses are found, return a 404 with a message
    if not expenses:
        return jsonify({"message": "No expenses found for this user"}), 404

    # Calculate total expenses by category
    categories = {}
    for e in expenses:
        if e.category in categories:
            categories[e.category] += e.amount
        else:
            categories[e.category] = e.amount

    # Prepare the response data
    expense_data = [{"category": category, "amount": amount} for category, amount in categories.items()]

    # Return the expense data as JSON
    return jsonify(expense_data)

# Upload Receipt Route (with OCR)
@main.route('/upload_receipt', methods=['GET', 'POST'])
@login_required
def upload_receipt():
    processed_image = None  # Default

    if request.method == 'POST':
        file = request.files.get('receipt')

        if not file or file.filename == '':
            flash('Please upload a valid image file.', 'danger')
            return redirect(url_for('main.upload_receipt'))

        filename = secure_filename(file.filename)
        uploads_dir = os.path.join('app', 'static', 'uploads')  # Correct folder path
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, filename)
        file.save(file_path)

        try:
            extracted_text = perform_ocr(file_path)
            parsed_date, amount, category, description = parse_receipt_text(extracted_text)

            new_expense = Expense(
                user_id=current_user.id,
                date=parsed_date,
                amount=amount,
                category=category,
                description=description
            )
            db.session.add(new_expense)
            db.session.commit()

            flash('Receipt processed successfully!', 'success')

            # Set the processed image path correctly for rendering in HTML
            processed_image = f'uploads/{filename}'

        except Exception as e:
            flash(f'Error processing receipt: {e}', 'danger')

    return render_template('upload_receipt.html', processed_image=processed_image)

# Visualize Expenses Route
@main.route('/visualize')
@login_required
def visualize():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    category_totals = {}
    for exp in expenses:
        category_totals[exp.category] = category_totals.get(exp.category, 0) + exp.amount
    data = [{'category': k, 'total': v} for k, v in category_totals.items()]
    return render_template('visualize.html', data=data)

# About Page Route
@main.route('/about')
def about():
    return render_template('about.html')

def save_expense(expense_data, user_id):
    try:
        print("🎤 Voice command received, calling save_expense...")

        with current_app.app_context():
            print(f"👤 DEBUG: Received user ID: {user_id}")

            user = User.query.get(user_id)
            if not user:
                print(f"❌ ERROR: User with ID {user_id} not found!")
                return False

            print(f"📌 DEBUG: Expense Data - {expense_data}")

            # Ensure all required fields are present
            required_fields = ["date", "amount", "category", "description"]
            if not all(key in expense_data for key in required_fields):
                print(f"❌ ERROR: Missing essential expense fields! Received: {list(expense_data.keys())}")
                return False

            # Ensure amount is properly formatted
            try:
                amount = float(expense_data["amount"])
                if amount <= 0:
                    raise ValueError("Amount must be greater than zero")
            except ValueError as e:
                print(f"❌ ERROR: Invalid amount format - {expense_data['amount']}. Error: {e}")
                return False

            # Convert date string to Python date object
            try:
                parsed_date = datetime.strptime(expense_data["date"], "%Y-%m-%d").date()
            except ValueError as e:
                print(f"❌ ERROR: Invalid date format - {expense_data['date']}. Error: {e}")
                return False

            # Check if expense already exists (optional duplicate prevention)
            existing_expense = Expense.query.filter_by(
                user_id=user_id, 
                date=parsed_date, 
                amount=amount, 
                category=expense_data["category"], 
                description=expense_data["description"]
            ).first()

            if existing_expense:
                print("⚠️ WARNING: Duplicate expense detected. Skipping save.")
                return False

            # Creating new expense entry
            new_expense = Expense(
                user_id=user_id,
                date=parsed_date,
                category=expense_data["category"],
                amount=amount,
                description=expense_data["description"]
            )

            count_before = Expense.query.count()
            print(f"📊 Expenses in DB before adding: {count_before}")

            db.session.add(new_expense)
            db.session.commit()

            count_after = Expense.query.count()
            print(f"✅ Expense committed! New count: {count_after}, Expense ID: {new_expense.id}")

            # Verify that the expense has been saved
            latest_expense = Expense.query.order_by(Expense.id.desc()).first()
            print(f"🔍 DEBUG: Latest saved expense -> {latest_expense}")

            return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR saving expense: {e}")
        import traceback
        print(traceback.format_exc())
        return False