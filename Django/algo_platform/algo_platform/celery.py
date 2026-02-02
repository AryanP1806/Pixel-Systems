import os
from celery import Celery

# 1. Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('algo_platform')

# 2. Load config from Django settings using 'CELERY' namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# 3. Auto-discover tasks in all apps (trading/tasks.py, etc.)
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')