from django.utils import timezone
from .models import UserProfile

class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Get or create the profile safely
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            
            # Check if we need to update (Throttling Logic)
            should_update = False
            now = timezone.now()
            
            if not profile.last_activity:
                should_update = True
            else:
                # Calculate seconds since last update
                diff = (now - profile.last_activity).total_seconds()
                # Only update if more than 5 minutes (300 seconds) have passed
                if diff > 300:
                    should_update = True
            
            if should_update:
                profile.last_activity = now
                # Update ONLY this field to keep it fast
                profile.save(update_fields=['last_activity'])
            
        response = self.get_response(request)
        return response