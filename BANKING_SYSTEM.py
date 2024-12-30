import sqlite3
import random
from datetime import datetime

DB_FILE = "banking_system.db"

def db_connect():
    return sqlite3.connect(DB_FILE)

# Database Setup
def setup_database():
    with db_connect() as conn:
        cursor = conn.cursor()

        # Create users table
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                account_number TEXT UNIQUE NOT NULL,
                dob TEXT NOT NULL,
                city TEXT NOT NULL,
                contact_number TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                address TEXT NOT NULL,
                balance REAL NOT NULL CHECK(balance >= 2000)
            )
        ''')

        # Create login table
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS login (
                user_id INTEGER PRIMARY KEY,
                password TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

        # Create transaction table
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS "transaction" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()

# User Management and Validation
def generate_account_number():
    return str(random.randint(1000000000, 9999999999))  # Generates a 10-digit unique account number

def add_user():
    while True:
        name = input("Enter your name: ").strip()
        if not name:
            print("Invalid input. Name cannot be empty.")
            continue

        while True:
            dob = input("Enter your date of birth (dd-MM-yyyy): ").strip()
            try:
                datetime.strptime(dob, "%d-%m-%Y")
                break
            except ValueError:
                print("Invalid date of birth format. Please use dd-MM-yyyy.")

        city = input("Enter your city: ").strip()
        if not city:
            print("Invalid input. City cannot be empty.")
            continue

        while True:
            contact_number = input("Enter your contact number (must start with 6, 7, 8, or 9 and be 10 digits): ").strip()
            if len(contact_number) == 10 and contact_number.isdigit() and contact_number.startswith(('6', '7', '8', '9')):
                break
            print("Invalid contact number. Must be 10 digits and start with 6, 7, 8, or 9.")

        while True:
            email = input("Enter your email (must end with @gmail.com): ").strip().lower()
            if email.endswith("@gmail.com"):
                break
            print("Invalid email. Must end with @gmail.com.")

        address = input("Enter your address: ").strip()
        if not address:
            print("Invalid input. Address cannot be empty.")
            continue

        while True:
            try:
                password = input("Enter your password: ").strip()
                if password:
                    break
                print("Password cannot be empty.")
            except ValueError:
                print("Invalid password. Try again.")

        while True:
            try:
                balance = float(input("Enter initial balance (min 2000): ").strip())
                if balance >= 2000:
                    break
                print("Initial balance must be at least 2000.")
            except ValueError:
                print("Invalid input. Balance must be a number.")

        # Generate a unique account number
        account_number = generate_account_number()

        # Add user to database
        with db_connect() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(''' 
                    INSERT INTO users (name, account_number, dob, city, contact_number, email, address, balance)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, account_number, dob, city, contact_number, email, address, balance))

                cursor.execute(''' 
                    INSERT INTO login (user_id, password) 
                    VALUES ((SELECT id FROM users WHERE account_number = ?), ?)
                ''', (account_number, password))

                conn.commit()
                print(f"User registered successfully with account number: {account_number}")
                break

            except sqlite3.IntegrityError as e:
                print(f"Database error: {e}. Please try again.")

def show_user():
    account_number = input("Enter account number to view details: ").strip()
    
    with db_connect() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, account_number, dob, city, contact_number, email, address, balance
            FROM users
            WHERE account_number = ?
        ''', (account_number,))
        user = cursor.fetchone()
        
    if user:
        print(f"\nUser Details:\nName: {user[1]}\nAccount Number: {user[2]}\nDate of Birth: {user[3]}\nCity: {user[4]}\n"
              f"Contact Number: {user[5]}\nEmail: {user[6]}\nAddress: {user[7]}\nBalance: {user[8]}")
    else:
        print("User not found!")

# Login and Banking Operations
def login():
    account_number = input("Enter your account number: ").strip()
    password = input("Enter your password: ").strip()

    with db_connect() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT users.id, login.is_active, users.balance 
            FROM users 
            JOIN login ON users.id = login.user_id
            WHERE users.account_number = ? AND login.password = ?
        ''', (account_number, password))
        
        user = cursor.fetchone()

    if user:
        if user[1] == 0:
            print("Account is deactivated.")
            return None
        print(f"Login successful! Your balance is {user[2]}")
        return user[0]
    else:
        print("Invalid account number or password.")
        return None

def show_balance(user_id):
    with db_connect() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE id = ?', (user_id,))
        balance = cursor.fetchone()[0]
        print(f"Your balance: {balance}")

def transaction_history(user_id):
    with db_connect() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT type, amount, timestamp 
            FROM "transaction" 
            WHERE user_id = ?
        ''', (user_id,))
        transactions = cursor.fetchall()

    if transactions:
        print("\nTransaction History:")
        for t in transactions:
            print(f"{t[2]} - {t[0]}: {t[1]}")
    else:
        print("No transactions found.")

# Banking Operations (Credit, Debit, Transfer, etc.)
def credit_amount(user_id):
    amount = float(input("Enter amount to credit: ").strip())
    if amount <= 0:
        print("Amount should be greater than zero.")
        return

    with db_connect() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, user_id))
        cursor.execute('INSERT INTO "transaction" (user_id, type, amount) VALUES (?, ?, ?)', (user_id, 'Credit', amount))
        conn.commit()

    print(f"{amount} credited successfully!")

def debit_amount(user_id):
    amount = float(input("Enter amount to debit: ").strip())
    if amount <= 0:
        print("Amount should be greater than zero.")
        return

    with db_connect() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE id = ?', (user_id,))
        balance = cursor.fetchone()[0]
        
        if balance >= amount:
            cursor.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, user_id))
            cursor.execute('INSERT INTO "transaction" (user_id, type, amount) VALUES (?, ?, ?)', (user_id, 'Debit', amount))
            conn.commit()
            print(f"{amount} debited successfully!")
        else:
            print("Insufficient balance!")

# Main Menu
def main():
    setup_database()

    current_user_id = None
    while True:
        print("\n1. Add User\n2. Show User\n3. Login\n4. Exit")
        choice = input("Select an option: ").strip()

        if choice == '1':
            add_user()
        elif choice == '2':
            show_user()
        elif choice == '3':
            current_user_id = login()
            if current_user_id:
                while True:
                    print("\n1. Show Balance\n2. Transaction History\n3. Credit Amount\n4. Debit Amount\n9. Logout")
                    action_choice = input("Select an action: ").strip()

                    if action_choice == '1':
                        show_balance(current_user_id)
                    elif action_choice == '2':
                        transaction_history(current_user_id)
                    elif action_choice == '3':
                        credit_amount(current_user_id)
                    elif action_choice == '4':
                        debit_amount(current_user_id)
                    elif action_choice == '9':
                        print("Logged out successfully!")
                        current_user_id = None
                        break
                    else:
                        print("Invalid choice, please try again.")
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid option. Try again.")

if __name__ == "__main__":
    main()
