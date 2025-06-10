import flet as ft
import sqlite3
import hashlib
import ctypes
import os
import sys

if sys.platform == "win32":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.yourname.preppal.1.0")

def get_app_data_path():
    base = os.getenv("LOCALAPPDATA") or os.path.expanduser("~/.myapp")
    path = os.path.join(base, "PrepPal")
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
    page.bgcolor = "#FFFFFF"

    page.bgcolor = None
    page.background_image = "Background.jpg"

    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.title = "PrepPal - Login"
    page.clean()

    username_field = ft.TextField(label="Username", width=350, bgcolor="#000000", color="white", border_radius=8)
    password_field = ft.TextField(label="Password", width=350, password=True, bgcolor="#000000", color="white", border_radius=8)
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

    button_style = ft.ButtonStyle(
        bgcolor="#E4956E",  # skin color
        color="black",
        shape=ft.RoundedRectangleBorder(radius=10),
        elevation=6,
        padding=ft.padding.symmetric(vertical=15),
    )

    login_button = ft.ElevatedButton(
        "Login",
        on_click=handle_login,
        width=350,
        style=button_style,
    )

    signup_button = ft.TextButton(
        "Create an account",
        on_click=lambda e: (page.clean(), signup_ui(page)),
        style=ft.ButtonStyle(color="#E4956E")
    )

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("PrepPal", size=32, weight=ft.FontWeight.BOLD, color="#E4956E"),
                username_field,
                password_field,
                login_button,
                signup_button,
                message_text
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=30,
            width=420,
            bgcolor="#000000",
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=15, color="#222222")
        )
    )

def signup_ui(page: ft.Page):
    page.clean()
    page.title = "PrepPal - Signup"

    username_field = ft.TextField(label="Username", width=350, bgcolor="#000000", color="white", border_radius=8)
    password_field = ft.TextField(label="Password", width=350, password=True, bgcolor="#000000", color="white", border_radius=8)
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

    button_style = ft.ButtonStyle(
        bgcolor="#E4956E",  # skin color
        color="black",
        shape=ft.RoundedRectangleBorder(radius=10),
        elevation=6,
        padding=ft.padding.symmetric(vertical=15),
    )

    signup_button = ft.ElevatedButton(
        "Signup",
        on_click=handle_signup,
        width=350,
        style=button_style,
    )

    login_button = ft.TextButton(
        "Already have an account? Login",
        on_click=lambda e: (page.clean(), login_ui(page)),
        style=ft.ButtonStyle(color="#E4956E")
    )

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("Create Account", size=32, weight=ft.FontWeight.BOLD, color="#E4956E"),
                username_field,
                password_field,
                signup_button,
                login_button,
                message_text
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=30,
            width=420,
            bgcolor="#000000",
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=15, color="#222222")
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
    page.title = "PrepPal"
    page.bgcolor = None
    page.background_image = "Background.jpg"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.clean()

    button_style = ft.ButtonStyle(
        bgcolor="#E4956E",
        color="black",
        shape=ft.RoundedRectangleBorder(radius=10),
        padding=ft.padding.symmetric(vertical=18),
        elevation=6,
    )

    layout = ft.Column([
        ft.Text("PrepPal", size=32, weight=ft.FontWeight.BOLD, color="#E4956E"),
        ft.Text(f"Welcome, {username}!", size=24, weight=ft.FontWeight.BOLD, color="#E4956E"),
        ft.ElevatedButton("Summarize notes", on_click=lambda e: launch_summarize_notes(page), style=button_style, width=380),
        ft.ElevatedButton("Clarify Doubts", on_click=lambda e: launch_clarify_doubts(page), style=button_style, width=380),
        ft.ElevatedButton("Practice Questions", on_click=lambda e: launch_practice_questions(page), style=button_style, width=380),
        ft.ElevatedButton("Logout", on_click=lambda e: logout(page), style=ft.ButtonStyle(color="white", bgcolor="#B00020"), width=100)
    ], spacing=20, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    page.add(
        ft.Container(
            content=layout,
            padding=30,
            width=420,
            bgcolor="#000000",
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=15, color="#222222")
        )
    )

def logout(page: ft.Page):
    try:
        path = get_credentials_path()
        if os.path.exists(path):
            os.chmod(path, 0o666)
            os.remove(path)
    except Exception as e:
        print(f"Failed to clear session: {e}")
    login_ui(page)

def launch_summarize_notes(page: ft.Page):
    from SummarizeNotes import SummarizeNotes
    view = ft.View(route="/summarize-notes", controls=[], bgcolor="#E3F2FD", scroll=ft.ScrollMode.AUTO)
    SummarizeNotes(page, view)
    page.views.append(view)
    page.go("/summarize-notes")

def launch_clarify_doubts(page: ft.Page):
    from ClarifyDoubts import ClarifyDoubts
    view = ft.View(route="/clarify-doubts", controls=[], bgcolor="#E3F2FD", scroll=ft.ScrollMode.AUTO)
    ClarifyDoubts(page, view)
    page.views.append(view)
    page.go("/clarify-doubts")

def launch_practice_questions(page: ft.Page):
    from PracticeQuestions import PracticeQuestions
    view = ft.View(route="/practice-questions", controls=[], bgcolor="#E3F2FD", scroll=ft.ScrollMode.AUTO)
    PracticeQuestions(page, view)
    page.views.append(view)
    page.go("/practice-questions")

def main(page: ft.Page):
    initialize_database()
    main_page(page)

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")