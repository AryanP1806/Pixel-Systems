# import logging
# import os
# import json
# from datetime import datetime
# from django.conf import settings
# from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
# from django.contrib.contenttypes.models import ContentType

# # --- 1. FILE LOGGING SETUP (Standard) ---
# LOG_DIR = os.path.join(settings.BASE_DIR, 'logs')
# os.makedirs(LOG_DIR, exist_ok=True)

# logger = logging.getLogger('site_logger')
# logger.setLevel(logging.INFO)

# log_file = os.path.join(LOG_DIR, f"site_{datetime.now().strftime('%Y-%m-%d')}.log")
# file_handler = logging.FileHandler(log_file)
# formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# file_handler.setFormatter(formatter)

# if not logger.handlers:
#     logger.addHandler(file_handler)

# # --- 2. SMART LOGGING FUNCTION ---
# def log_action(user, action, obj_type, obj_id=None, changes=None, object_repr=None):
#     """
#     Logs detailed changes to both a text file and the Django Database.
    
#     :param changes: list or dict of specific field changes (e.g., "Email changed from X to Y")
#     :param object_repr: Human-readable name (e.g., "Customer: John Doe")
#     """
    
#     username = user.username if user and hasattr(user, "username") else "System"
    
#     # A. Format the 'Changes' for readability
#     change_text = ""
#     if changes:
#         if isinstance(changes, list):
#             change_text = " | ".join(changes)
#         elif isinstance(changes, dict):
#             # Convert dict to readable string
#             change_text = " | ".join([f"{k}: {v}" for k, v in changes.items()])
#         else:
#             change_text = str(changes)

#     # B. Construct File Log Message
#     parts = [f"User: {username}", f"Action: {action}", f"Object: {obj_type}"]
#     if obj_id: parts.append(f"ID: {obj_id}")
#     if object_repr: parts.append(f"Ref: {object_repr}")
#     if change_text: parts.append(f"Updates: [{change_text}]") # <--- The details you were missing

#     logger.info(" | ".join(parts))

#     # C. Write to Database (for Dashboard)
#     if user and hasattr(user, 'pk'):
#         try:
#             # Determine Flag
#             action_lower = action.lower()
#             if any(x in action_lower for x in ['add', 'create', 'new']):
#                 flag = ADDITION
#             elif any(x in action_lower for x in ['delete', 'remove']):
#                 flag = DELETION
#             else:
#                 flag = CHANGE

#             # Get ContentType
#             try:
#                 ct = ContentType.objects.filter(model__iexact=obj_type).first()
#                 if not ct: ct = ContentType.objects.get_for_model(LogEntry)
#             except:
#                 ct = ContentType.objects.get_for_model(LogEntry)

#             # Save to DB
#             LogEntry.objects.log_action(
#                 user_id=user.pk,
#                 content_type_id=ct.pk,
#                 object_id=obj_id or 0,
#                 object_repr=object_repr or str(obj_id),
#                 action_flag=flag,
#                 change_message=change_text[:250] if change_text else action # Truncate if too long
#             )
#         except Exception as e:
#             logger.error(f"DB Log Error: {e}")
# new
import logging
import os
import sys
from datetime import datetime
from django.conf import settings
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType

# --- 1. SETUP LOGGING ---
logger = logging.getLogger('site_logger')
logger.setLevel(logging.INFO)

# Clear existing handlers to prevent duplicates on server reload
if logger.hasHandlers():
    logger.handlers.clear()

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# --- STRATEGY A: File Logging (The "Nice to Have") ---
try:
    # Ensure BASE_DIR is a string, sometimes Django uses Path objects
    base_dir_str = str(settings.BASE_DIR)
    
    LOG_DIR = os.path.join(base_dir_str, 'logs')
    os.makedirs(LOG_DIR, exist_ok=True)

    log_file = os.path.join(LOG_DIR, f"site_{datetime.now().strftime('%Y-%m-%d')}.log")
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
except Exception as e:
    # If file creation fails, print to system error log so you know why
    print(f"CRITICAL LOGGER ERROR: Could not create log file: {e}", file=sys.stderr)

# --- STRATEGY B: Console Logging (The "Fail-Safe") ---
# This ensures logs appear in your PythonAnywhere 'Server Log' tab
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


# --- 2. SMART LOGGING FUNCTION ---
def log_action(user, action, obj_type, obj_id=None, changes=None, object_repr=None):
    """
    Logs detailed changes to:
    1. Text File (logs/site_YYYY-MM-DD.log)
    2. Console (PythonAnywhere Server Log)
    3. Django Admin Database (LogEntry)
    """
    
    username = user.username if user and hasattr(user, "username") else "System"
    
    # A. Format the 'Changes' for readability
    change_text = ""
    if changes:
        if isinstance(changes, list):
            change_text = " | ".join(changes)
        elif isinstance(changes, dict):
            change_text = " | ".join([f"{k}: {v}" for k, v in changes.items()])
        else:
            change_text = str(changes)

    # B. Construct Log Message
    parts = [f"User: {username}", f"Action: {action}", f"Object: {obj_type}"]
    if obj_id: parts.append(f"ID: {obj_id}")
    if object_repr: parts.append(f"Ref: {object_repr}")
    if change_text: parts.append(f"Updates: [{change_text}]")

    final_msg = " | ".join(parts)
    
    # Write to File & Console
    logger.info(final_msg)

    # C. Write to Database (LogEntry)
    if user and hasattr(user, 'pk'):
        try:
            # Determine Flag
            action_lower = action.lower()
            if any(x in action_lower for x in ['add', 'create', 'new']):
                flag = ADDITION
            elif any(x in action_lower for x in ['delete', 'remove']):
                flag = DELETION
            else:
                flag = CHANGE

            # Get ContentType
            try:
                ct = ContentType.objects.filter(model__iexact=obj_type).first()
                if not ct: 
                    # Fallback if model name doesn't match exactly
                    ct = ContentType.objects.get_for_model(LogEntry)
            except:
                ct = ContentType.objects.get_for_model(LogEntry)

            # Save to DB
            LogEntry.objects.log_action(
                user_id=user.pk,
                content_type_id=ct.pk,
                object_id=obj_id or 0,
                object_repr=object_repr or str(obj_id),
                action_flag=flag,
                change_message=change_text[:250] if change_text else action
            )
        except Exception as e:
            # Log DB errors to the console/file so we don't crash the app
            logger.error(f"DB Log Error: {e}")