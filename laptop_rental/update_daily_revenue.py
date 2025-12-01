import os
import sys
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

# ✅ Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laptop_rental.settings")

import django
django.setup()

from rentals.models import Rental, ProductAsset


def update_revenue_for_rentals():
    """
    Update revenue for all rentals:
    - Reset all product revenues to 0 first.
    - Calculate total revenue from rental_start_date to today or rental_end_date.
    - Works correctly even if run multiple times a day.
    """
    today = date.today()

    # ✅ Step 1: Reset revenue for all products to 0
    ProductAsset.objects.update(revenue=Decimal('0.00'))

    updated_rentals = 0

    # ✅ Step 2: Get all rentals with a payment amount
    rentals = Rental.objects.filter(payment_amount__gt=0)

    for rental in rentals:
        # Skip rentals starting in the future
        if rental.rental_start_date > today:
            continue

        # Determine the effective end date
        end_date = rental.rental_end_date if rental.rental_end_date else today

        # Don't calculate beyond today
        if end_date > today:
            end_date = today

        # Initialize total revenue for this rental
        total_rental_revenue = Decimal('0.00')

        current_date = rental.rental_start_date

        # Loop through months between start and end
        while current_date <= end_date:
            # Calculate days in current month
            if current_date.month == 12:
                next_month_start = date(current_date.year + 1, 1, 1)
            else:
                next_month_start = date(current_date.year, current_date.month + 1, 1)

            days_in_month = (next_month_start - timedelta(days=1)).day

            # Daily rate
            daily_rate = (rental.payment_amount / Decimal(days_in_month)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Days to count for this month
            start_day = current_date.day
            end_day = min(end_date.day if current_date.month == end_date.month and current_date.year == end_date.year else days_in_month, days_in_month)

            days_to_count = end_day - start_day + 1

            total_rental_revenue += (daily_rate * Decimal(days_to_count)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Move to first day of next month
            current_date = next_month_start

        # ✅ Add to product's total revenue
        if rental.asset:
            before = rental.asset.revenue
            rental.asset.revenue += total_rental_revenue
            rental.asset.save()

            print(f"[{rental.asset.asset_id}] Before: {before} | Added: {total_rental_revenue} | After: {rental.asset.revenue}")
            updated_rentals += 1

    print(f"\nSuccessfully recalculated revenue for {updated_rentals} rentals as of {today}.")


if __name__ == "__main__":
    update_revenue_for_rentals()
