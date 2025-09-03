from .models import Product, Order, CartItem
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.conf import settings

def product_list(request):
    products = Product.objects.all()
    return render(request, 'shop/products.html', {'products': products})


@login_required
def view_cart(request):
    items = CartItem.objects.filter(user=request.user)
    return render(request, 'shop/cart.html', {'cart_items': items})


@login_required
def order_product(request, product_id):
    product = Product.objects.get(id=product_id)
    Order.objects.create(user=request.user, product=product, quantity=1)
    return redirect('shop:products')


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('shop:cart')

@login_required
def checkout(request):
    cart = CartItem.objects.filter(user=request.user)

    if not request.user.profile.city in ['Pune', 'Mumbai']:
        return HttpResponse("Sorry, delivery not available in your area.")

    if not cart.exists():
        return redirect('shop:cart')

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        confirmed = request.POST.get('confirm')  # This is only set after clicking "I've Paid"

        # STEP 1 — If GPay and not confirmed yet, show QR code
        if payment_method == 'GPay' and not confirmed:
            return render(request, 'shop/checkout.html', {
                'cart_items': cart,
                'show_qr': True
            })

        # STEP 2 — Payment confirmed OR Cash on Delivery
        for item in cart:
            Order.objects.create(
                user=request.user,
                product=item.product,
                quantity=item.quantity,
                payment_method=payment_method
            )
            item.delete()

        # Send confirmation email
        send_mail(
            subject='🐾 Order Confirmed - Pawssible',
            message=f'''
Dear {request.user.username},

Thank you for your order!

Payment Method: {payment_method}
Your order has been placed and is now being processed.

Pawssibly yours,
The Pawssible Team
''',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[request.user.email],
            fail_silently=False,
        )

        return render(request, 'shop/thank_you.html', {'method': payment_method})

    return render(request, 'shop/checkout.html', {'cart_items': cart})
