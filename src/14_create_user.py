import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db

db.init_db()

username = input("Username: ").strip()
password = getpass.getpass("Password (hidden): ")
confirm = getpass.getpass("Repeat password: ")

if password != confirm:
    sys.exit("Passwords do not match.")

try:
    db.create_user(username, password, role="admin")
except ValueError as error:
    sys.exit(f"Could not create user: {error}")

print("User created:", username)