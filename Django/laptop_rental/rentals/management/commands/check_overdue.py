# # rentals/management/commands/check_overdue.py

# from django.core.management.base import BaseCommand
# from django.core.mail import send_mail
# from django.utils import timezone
# from rentals.models import Rental

# class Command(BaseCommand):
#     help = 'Mark rentals as overdue and send email notifications'

#     def handle(self, *args, **kwargs):
#         today = timezone.now().date()
#         rentals = Rental.objects.filter(status='ongoing')

#         for rental in rentals:
#             due_date = rental.rental_start_date + timezone.timedelta(days=rental.duration_days)
#             if due_date < today:
#                 rental.status = 'overdue'
#                 rental.save()

#                 try:
#                     send_mail(
#                         subject='Rental Overdue Notification',
#                         message=f'Rental for {rental.customer.name} is overdue.\nAsset ID: {rental.asset.asset_id}',
#                         from_email='aryanpore3056@gmail.com',
#                         recipient_list=['aryanpore3056@gmail.com'],
#                         fail_silently=False,
#                     )
#                 except Exception as e:
#                     self.stderr.write(f"Failed to send email: {e}")

#         self.stdout.write(self.style.SUCCESS('Checked and updated overdue rentals.'))
