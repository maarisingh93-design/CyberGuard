import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db

username = input("Username: ").strip()
password = getpass.getpass("Password (hidden): ")

user = db.verify_user(username, password)
if user:
    print("Login OK:", user)
else:
    print("Login FAILED")