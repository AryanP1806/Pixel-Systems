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

# def log_action(user, action, obj_type, obj_id=None, extra=None):
#     """
#     Record user actions or system events.
#     """
#     message = f"User: {user.username if user else 'System'} | Action: {action} | Object: {obj_type}"
#     if obj_id:
#         message += f" | ID: {obj_id}" 
#     if extra:
#         message += f" | Details: {extra}"
#     logger.info(message)


def log_action(
    user,
    action,
    obj_type,
    obj_id=None,
    asset=None,
    customer=None,
    extra=None
):
    """
    Universal structured audit logger.
    """

    username = user.username if user and hasattr(user, "username") else "System"

    parts = [
        f"User: {username}",
        f"Action: {action}",
        f"Object: {obj_type}",
    ]

    if obj_id:
        parts.append(f"ObjectID: {obj_id}")

    # ✅ ASSET CONTEXT (MOST IMPORTANT FOR YOU)
    if asset:
        try:
            parts.append(f"AssetID: {asset.asset_id}")
        except:
            parts.append(f"AssetID: {asset}")

    # ✅ CUSTOMER CONTEXT
    if customer:
        try:
            parts.append(f"Customer: {customer.name}")
        except:
            parts.append(f"Customer: {customer}")

    # ✅ EXTRA DETAILS (contract, revenue, etc.)
    if extra:
        parts.append(f"Details: {extra}")

    message = " | ".join(parts)

    logger.info(message)
