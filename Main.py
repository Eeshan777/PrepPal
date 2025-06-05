import flet as ft
import sqlite3
import hashlib
import ctypes
import os
import sys

if sys.platform == "win32":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.yourname.personalfinance.1.0")

def get_app_data_path():
    base = os.getenv("LOCALAPPDATA") or os.path.expanduser("~/.myapp")
    path = os.path.join(base, "PersonalFinance")
    os.makedirs(path, exist_ok=True)
    return path

def get_credentials_path():
    base = get_app_data_path()
    path = os.path.join(base, "credentials.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

def get_db_path():
    base = get_app_data_path()
    path = os.path.join(base, "database.db")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

def hide_file_windows(filepath):
    if sys.platform == "win32":
        try:
            ctypes.windll.kernel32.SetFileAttributesW(str(filepath), 0x02)
        except:
            pass

def initialize_database():
    with sqlite3.connect(get_db_path()) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')
        conn.commit()

def validate_credentials(username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    with sqlite3.connect(get_db_path()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, hashed_password))
        return cursor.fetchone() is not None

def save_session(username):
    path = get_credentials_path()
    try:
        if os.path.exists(path):
            os.chmod(path, 0o666)
            os.remove(path)
        with open(path, "w") as f:
            f.write(username)
        hide_file_windows(path)
    except Exception as e:
        print(f"Failed to save session: {e}")

def load_session():
    try:
        with open(get_credentials_path(), "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def login_ui(page: ft.Page):
    page.window_maximized = True
    page.window_full_screen = True
    page.scroll = ft.ScrollMode.AUTO
    page.update()
    page.clean()
    page.title = "Personal Finance - Login"
    page.bgcolor = "#E3F2FD"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    username_field = ft.TextField(label="Username", width=350, bgcolor="#FFFFFF", border_radius=8, color="black")
    password_field = ft.TextField(label="Password", width=350, password=True, bgcolor="#FFFFFF", border_radius=8, color="black")
    message_text = ft.Text("", color="red")

    def handle_login(e):
        username = username_field.value.strip()
        password = password_field.value.strip()
        if validate_credentials(username, password):
            save_session(username)
            page.clean()
            setup_main_ui(page, username)
        else:
            message_text.value = "Invalid credentials"
            page.update()

    def handle_enter(e):
        if e.control == username_field:
            password_field.focus()
        elif e.control == password_field:
            handle_login(None)

    username_field.on_submit = handle_enter
    password_field.on_submit = handle_enter

    login_button = ft.ElevatedButton("Login", on_click=handle_login, bgcolor="#1565C0", style=ft.ButtonStyle(color="white"), width=350)
    signup_button = ft.TextButton(
        "Create an account",
        on_click=lambda e: (page.clean(), signup_ui(page)),
        style=ft.ButtonStyle(color="#1565C0")
    )

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("Personal Finance", size=30, weight=ft.FontWeight.BOLD, color="#0D47A1"),
                username_field,
                password_field,
                login_button,
                signup_button,
                message_text
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=30,
            width=400,
            bgcolor="white",
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=15, color="#B0BEC5")
        )
    )

def signup_ui(page: ft.Page):
    page.clean()
    page.title = "Personal Finance - Signup"

    username_field = ft.TextField(label="Username", width=350, bgcolor="#FFFFFF", border_radius=8, color="black")
    password_field = ft.TextField(label="Password", width=350, password=True, bgcolor="#FFFFFF", border_radius=8, color="black")
    message_text = ft.Text("", color="red")

    def handle_signup(e):
        username = username_field.value.strip()
        password = password_field.value.strip()

        if len(password) < 6:
            message_text.value = "Password must be at least 6 characters."
        elif check_username_exists(username):
            message_text.value = "Username already taken."
        else:
            hashed = hashlib.sha256(password.encode()).hexdigest()
            with sqlite3.connect(get_db_path()) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
                conn.commit()
            login_ui(page)
        page.update()

    username_field.on_submit = lambda e: password_field.focus()
    password_field.on_submit = handle_signup

    signup_button = ft.ElevatedButton("Signup", on_click=handle_signup, bgcolor="#2E7D32", style=ft.ButtonStyle(color="white"), width=350)
    login_button = ft.TextButton(
        "Already have an account? Login",
        on_click=lambda e: (page.clean(), login_ui(page)),
        style=ft.ButtonStyle(color="#1565C0")
    )

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("Create Account", size=30, weight=ft.FontWeight.BOLD, color="#1B5E20"),
                username_field,
                password_field,
                signup_button,
                login_button,
                message_text
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=30,
            width=400,
            bgcolor="white",
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=15, color="#B0BEC5")
        )
    )

def check_username_exists(username):
    with sqlite3.connect(get_db_path()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=?", (username,))
        return cursor.fetchone() is not None

def main_page(page: ft.Page):
    page.window_maximized = True
    page.window_full_screen = True
    page.scroll = ft.ScrollMode.AUTO
    page.update()

    username = load_session()
    if username:
        page.clean()
        setup_main_ui(page, username)
    else:
        page.clean()
        login_ui(page)

def setup_main_ui(page: ft.Page, username: str):
    page.title = "Personal Finance"
    page.bgcolor = "#E3F2FD"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    button_style = ft.ButtonStyle(
        bgcolor="#1565C0",
        color="white",
        shape=ft.RoundedRectangleBorder(radius=10),
        padding=ft.padding.symmetric(vertical=20, horizontal=20),
        elevation=6,
    )

    layout = ft.Column([
        ft.Text("Personal Finance", size=30, weight=ft.FontWeight.BOLD, color="#0D47A1"),
        ft.Text(f"Welcome, {username}!", size=24, weight=ft.FontWeight.BOLD, color="#003366"),
        ft.ElevatedButton("Transaction Record", on_click=lambda e: launch_transaction_record(page), style=button_style, width=380),
        ft.ElevatedButton("Interest Calculator", on_click=lambda e: launch_interest_calculator(page), style=button_style, width=380),
        ft.ElevatedButton("Budget Report", on_click=lambda e: launch_budget_report(page), style=button_style, width=380),
        ft.ElevatedButton("Download PDF", on_click=lambda e: launch_download_pdf(page), style=button_style, width=380),
        ft.ElevatedButton("Logout", on_click=lambda e: logout(page), style=ft.ButtonStyle(color="white"), width=80, bgcolor="#FF0000")
    ], spacing=20, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    page.add(layout)

def logout(page: ft.Page):
    try:
        path = get_credentials_path()
        if os.path.exists(path):
            os.chmod(path, 0o666)
            os.remove(path)
    except Exception as e:
        print(f"Failed to clear session: {e}")
    login_ui(page)

def launch_transaction_record(page: ft.Page):
    from TransactionRecord import TransactionRecord
    view = ft.View(route="/transaction", controls=[], bgcolor="#E3F2FD", scroll=ft.ScrollMode.AUTO)
    TransactionRecord(page, view)
    page.views.append(view)
    page.go("/transaction")

def launch_interest_calculator(page: ft.Page):
    from InterestCalculator import InterestCalculator
    view = ft.View(route="/interest-calculator", controls=[], bgcolor="#E3F2FD", scroll=ft.ScrollMode.AUTO)
    InterestCalculator(page, view)
    page.views.append(view)
    page.go("/interest-calculator")

def launch_budget_report(page: ft.Page):
    from BudgetReport import BudgetReport
    view = ft.View(route="/budget-report", controls=[], bgcolor="#E3F2FD", scroll=ft.ScrollMode.AUTO)
    BudgetReport(page, view)
    page.views.append(view)
    page.go("/budget-report")

def launch_download_pdf(page: ft.Page):
    from DownloadPDF import DownloadPDF
    view = ft.View(route="/download-pdf", controls=[], bgcolor="#E3F2FD", scroll=ft.ScrollMode.AUTO)
    DownloadPDF(page, view)
    page.views.append(view)
    page.go("/download-pdf")

if __name__ == "__main__":
    initialize_database()
    ft.app(target=login_ui)