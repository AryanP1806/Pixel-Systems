from django import template

register = template.Library()

@register.filter
def rented_by(asset):
    """
    Returns the name of the customer who has rented this asset if it's ongoing,
    otherwise returns 'Available'.
    """
    ongoing_rental = asset.rentals.filter(status='ongoing').first()
    if ongoing_rental:
        return ongoing_rental.customer.name
    return "Available"
