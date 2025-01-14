from flask import Flask, render_template, request, redirect, url_for, flash, session
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a secure key for production

# Initialize Firebase
cred = credentials.Certificate(r"C:\Users\smily\OneDrive\Desktop\firebase\private.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Sample in-memory store for user's budget (you can replace this with a database)
user_budget = {}
monthly_budget = []

# Helper function to calculate monthly and yearly totals




@app.route("/")
def home():
    if "user_email" in session:
        user_email = session["user_email"]

        # Fetch transactions
        transactions_ref = db.collection("personal").where("user_email", "==", user_email).stream()
        transactions = []
        total_income = 0
        total_expenses = 0
        category_expenses = {}

        for transaction in transactions_ref:
            transaction_data = transaction.to_dict()
            transaction_data["id"] = transaction.id
            transaction_data["date"] = transaction_data["date"].strftime('%Y-%m-%d %H:%M:%S')
            transactions.append(transaction_data)

            if transaction_data["transaction_type"] == "Expense":
                total_expenses += transaction_data["amount"]
                category = transaction_data["category"]
                category_expenses[category] = category_expenses.get(category, 0) + transaction_data["amount"]
            elif transaction_data["transaction_type"] == "Income":
                total_income += transaction_data["amount"]

        # Fetch monthly budgets
        budgets_ref = db.collection("budgets").where("user_email", "==", user_email).stream()
        monthly_budgets = {}
        for budget in budgets_ref:
            budget_data = budget.to_dict()
            category = budget_data["category"]
            monthly_budgets[category] = budget_data["amount"]

        # Check budget notifications
        budget_notifications = []
        for category, spent in category_expenses.items():
            if category in monthly_budgets and spent > monthly_budgets[category]:
                budget_notifications.append(f"You have exceeded your budget for {category}. Budget: ${monthly_budgets[category]}, Spent: ${spent}")

        total_savings = total_income - total_expenses

        # Pass budget data to the template
        return render_template(
            "dashboard.html",
            transactions=transactions,
            total_income=total_income,
            total_expenses=total_expenses,
            total_savings=total_savings,
            budget_notifications=budget_notifications,
            monthly_budgets=monthly_budgets  # Pass the budget summary
        )
    return redirect(url_for("home"))



@app.route('/monthly_report')
def monthly_report():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    user_email = session['user_email']
    current_month = datetime.now().strftime("%Y-%m")  # Current month (YYYY-MM)

    # Fetch transactions from Firestore
    transactions_ref = db.collection('personal').where("user_email", "==", user_email).stream()
    transactions = []
    total_income = 0
    total_expenses = 0
    category_expenses = {}

    for transaction in transactions_ref:
        transaction_data = transaction.to_dict()
        transaction_date = transaction_data['date'].strftime('%Y-%m')  # Format to year-month
        
        if transaction_date == current_month:  # Filter for current month
            if transaction_data['transaction_type'] == 'Income':
                total_income += transaction_data['amount']
            elif transaction_data['transaction_type'] == 'Expense':
                total_expenses += transaction_data['amount']
                category = transaction_data['category']
                category_expenses[category] = category_expenses.get(category, 0) + transaction_data['amount']
    
    total_savings = total_income - total_expenses

    return render_template('report.html',
                           total_income=total_income, 
                           total_expenses=total_expenses, 
                           total_savings=total_savings,
                           category_expenses=category_expenses,
                           period='monthly', 
                           current_month=current_month)


@app.route('/yearly_report')
def yearly_report():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    user_email = session['user_email']
    current_year = datetime.now().strftime("%Y")  # Current year (YYYY)

    # Fetch transactions from Firestore
    transactions_ref = db.collection('personal').where("user_email", "==", user_email).stream()
    transactions = []
    total_income = 0
    total_expenses = 0
    category_expenses = {}

    for transaction in transactions_ref:
        transaction_data = transaction.to_dict()
        transaction_date = transaction_data['date'].strftime('%Y')  # Format to year
        
        if transaction_date == current_year:  # Filter for current year
            if transaction_data['transaction_type'] == 'Income':
                total_income += transaction_data['amount']
            elif transaction_data['transaction_type'] == 'Expense':
                total_expenses += transaction_data['amount']
                category = transaction_data['category']
                category_expenses[category] = category_expenses.get(category, 0) + transaction_data['amount']

    total_savings = total_income - total_expenses

    return render_template('report.html',
                           total_income=total_income, 
                           total_expenses=total_expenses, 
                           total_savings=total_savings,
                           category_expenses=category_expenses,
                           period='yearly', 
                           current_year=current_year)


@app.route('/set_budget', methods=['GET', 'POST'])
def set_budget():
    current_year = 2025  # Set the current year dynamically or through logic
    current_month = datetime.now().month  # Dynamically get the current month
    
    # Example general and monthly budgets data (replace with actual data retrieval logic)
    general_budget = {}
    monthly_budget_data = {}



    # Example monthly budget data (replace with actual data retrieval logic)
    monthly_budget = {category['category']: category['amount'] for category in monthly_budget_data}

    if request.method == 'POST':
        # Handle form submission logic for both general and monthly budget
        if 'category' in request.form:  # If it's the monthly budget form
            category = request.form['category']
            amount = request.form['amount']
            month = request.form['month']
            year = request.form['year']

            # Store monthly budget
            monthly_budget.update({'category': category, 'amount': amount, 'month': month, 'year': year})
        else:  # If it's the general budget form
            income = request.form['income']
            expenses = request.form['expenses']
            savings = request.form['savings']

            user_budget['income'] = income
            user_budget['expenses'] = expenses
            user_budget['savings'] = savings

        return redirect(url_for('set_budget'))

    return render_template('set_budget.html', 
                           general_budget=general_budget, 
                           monthly_budget=monthly_budget, 
                           current_month=current_month, 
                           current_year=current_year)


@app.route("/add", methods=["GET", "POST"])
def add_transaction():
    if request.method == "POST":
        user_email = session["user_email"]
        amount = float(request.form["amount"])
        description = request.form["description"]
        category = request.form["category"]
        transaction_type = request.form["transaction_type"]
        date = datetime.now()

        db.collection("personal").add({
            "user_email": user_email,
            "amount": amount,
            "description": description,
            "category": category,
            "transaction_type": transaction_type,
            "date": date
        })
        flash(f"{transaction_type} added successfully!", "success")
        return redirect(url_for("home"))

    return render_template("add_expense.html")


@app.route("/delete_transaction/<transaction_id>")
def delete_transaction(transaction_id):
    # Delete the transaction from Firestore
    db.collection("personal").document(transaction_id).delete()
    flash("Transaction deleted successfully!", "success")
    return redirect(url_for("home"))

@app.route("/edit_transaction/<transaction_id>", methods=["GET", "POST"])
def edit_transaction(transaction_id):
    transaction_ref = db.collection("personal").document(transaction_id)
    transaction = transaction_ref.get()

    if not transaction.exists:
        flash("Transaction not found!", "danger")
        return redirect(url_for("home"))

    transaction_data = transaction.to_dict()

    if request.method == "POST":
    # Get updated data from the form
        amount = float(request.form["amount"])
        description = request.form["description"]
        category = request.form["category"]
        transaction_type = request.form["transaction_type"]
        
        # Print or log the values to verify
        print(amount, description, category, transaction_type)
        
        # Update the transaction
        transaction_ref.update({
            "amount": amount,
            "description": description,
            "category": category,
            "transaction_type": transaction_type,
            "date": datetime.now()
        })
        print("Before update:", transaction_data)
        transaction_ref.update({
        "amount": amount,
        "description": description,
        "category": category,
        "transaction_type": transaction_type,
        "date": datetime.now()
    })
    updated_transaction = transaction_ref.get()
    print("After update:", updated_transaction.to_dict())


    # Render the edit form with the current data
    return render_template("update_transaction.html", transaction_data=transaction_data)


@app.route("/delete_budget/<budget_id>")
def delete_budget(budget_id):
    # Delete the budget from Firestore
    db.collection("budgets").document(budget_id).delete()
    flash("Budget deleted successfully!", "success")
    return redirect(url_for("home"))

@app.route("/edit_budget/<budget_id>", methods=["GET", "POST"])
def edit_budget(budget_id):
    budget_ref = db.collection("budgets").document(budget_id)
    budget = budget_ref.get()

    if not budget.exists:
        flash("Budget not found!", "danger")
        return redirect(url_for("home"))

    budget_data = budget.to_dict()

    if request.method == "POST":
        # Get updated data from the form
        amount = float(request.form["amount"])

        # Update the budget
        budget_ref.update({
            "amount": amount
        })
        flash("Budget updated successfully!", "success")
        return redirect(url_for("home"))

    # Render the edit form with the current data
    return render_template("edit_budget.html", budget_data=budget_data)



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user_ref = db.collection("users").where("email", "==", email).stream()
        user = next(user_ref, None)
        if user and user.to_dict()["password"] == password:
            session["user_email"] = email
            session["user_name"] = user.to_dict()["name"]
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid email or password!", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_email", None)
    session.pop("user_name", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
