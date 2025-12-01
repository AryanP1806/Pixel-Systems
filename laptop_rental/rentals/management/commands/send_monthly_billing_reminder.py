from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from rentals.models import Rental

class Command(BaseCommand):
    help = 'Send monthly rental billing reminder'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        # 🔁 Send only on specific day of the month (e.g., 5th)
        BILLING_DAY = 17
        if today.day != BILLING_DAY:
            self.stdout.write("Not billing day. Skipping email.")
            return

        # Get ongoing rentals
        ongoing_rentals = Rental.objects.filter(status='ongoing')
        if not ongoing_rentals.exists():
            self.stdout.write("No ongoing rentals found.")
            return

        # Prepare email content
        lines = ["Monthly Rental Billing Reminder\n"]
        for rental in ongoing_rentals:
            lines.append(
                f"- Customer: {rental.customer.name}\n"
                f"  Asset ID: {rental.asset.asset_id if rental.asset else 'N/A'}\n"
                f"  Contract #: {rental.contract_number or 'N/A'}\n"
                f"  Start Date: {rental.rental_start_date}\n"
                f"  Duration: {rental.duration_days} days\n"
                f"  ----------"
            )

        message = "\n".join(lines)

        try:
            send_mail(
                subject="Monthly Rental Billing Reminder",
                message=message,
                from_email='aryanpore3056@gmail.com',  # change this
                recipient_list=['aryanpore3056@gmail.com'],  # your email
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS("Reminder email sent."))
        except Exception as e:
            self.stderr.write(f"Error sending email: {e}")
