from calendar import monthrange
from datetime import date, timedelta
# utils.py

from calendar import monthrange
from datetime import date

def calculate_daily_rate(payment_amount, target_date=None):
    if not target_date:
        target_date = date.today()

    days_in_month = monthrange(target_date.year, target_date.month)[1]

    print(f"DEBUG: Payment = {payment_amount}, Days in month = {days_in_month}")  # Debug line

    return round(payment_amount / days_in_month, 2)

def calculate_rental_revenue(rental_start, rental_end, monthly_payment):
    """
    Calculate total revenue for a rental between start and end dates,
    pro-rated by the actual days in each month.
    """
    if not rental_end:
        rental_end = date.today()  # If rental is still active

    total_revenue = 0
    current_date = rental_start

    while current_date <= rental_end:
        # Days in the current month
        days_in_month = monthrange(current_date.year, current_date.month)[1]

        # Start and end boundaries for this month
        start_of_month = date(current_date.year, current_date.month, 1)
        end_of_month = date(current_date.year, current_date.month, days_in_month)

        # Actual active days in this month
        active_start = max(rental_start, start_of_month)
        active_end = min(rental_end, end_of_month)
        active_days = (active_end - active_start).days + 1  # inclusive

        # Calculate daily rate
        daily_rate = monthly_payment / days_in_month

        # Add this month's revenue
        total_revenue += active_days * daily_rate

        # Move to next month
        current_date = end_of_month + timedelta(days=1)

    return round(total_revenue, 2)


import logging
from datetime import datetime
from django.conf import settings
import os

# Define log directory
LOG_DIR = os.path.join(settings.BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logger
logger = logging.getLogger('site_logger')
logger.setLevel(logging.INFO)

# Log file with date
log_file = os.path.join(LOG_DIR, f"site_{datetime.now().strftime('%Y-%m-%d')}.log")
file_handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(file_handler)

def log_action(user, action, obj_type, obj_id=None, extra=None):
    """
    Record user actions or system events.
    """
    message = f"User: {user.username if user else 'System'} | Action: {action} | Object: {obj_type}"
    if obj_id:
        message += f" | ID: {obj_id}" 
    if extra:
        message += f" | Details: {extra}"
    logger.info(message)
