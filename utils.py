# utils.py

from config import ADMIN_IDS
from db import get_user

def is_admin(user_id):
    return user_id in ADMIN_IDS

def user_balance(telegram_id):
    user = get_user(telegram_id)
    if user:
        return user[3]  # balance column
    return 0
