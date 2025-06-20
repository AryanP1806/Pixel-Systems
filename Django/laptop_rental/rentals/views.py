from django.shortcuts import render
from .models import Rental, Customer, ProductUnit
from .forms import CustomerForm, ProductForm, RentalForm
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.db.models import Q


def homepage(request):
    return render(request, 'homepage.html')


def rental_list(request):
    rentals = Rental.objects.filter(status='ongoing')
    return render(request, 'rentals/rental_list.html', {'rentals': rentals})


def customer_list(request):
    query = request.GET.get('q')
    is_permanent = request.GET.get('permanent') == 'on'
    is_bni = request.GET.get('bni') == 'on'

    customers = Customer.objects.all()
    if query:
        customers = customers.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone_number_primary__icontains=query) |
            Q(phone_number_secondary__icontains=query)
        )

    if is_permanent:
        customers = customers.filter(is_permanent=True)

    if is_bni:
        customers = customers.filter(is_bni_member=True)

    return render(request, 'rentals/customer_list.html', {'customers': customers})


# def product_list(request):
#     products = ProductUnit.objects.all()
#     return render(request, 'rentals/product_list.html', {'products': products})



def product_list(request):
    products = ProductUnit.objects.select_related('model').all()
    return render(request, 'rentals/product_list.html', {'products': products})


def rental_history(request):
    history = Rental.objects.select_related('customer', 'unit').filter(status='completed')
    return render(request, 'rentals/rental_history.html', {'history': history})



def add_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'rentals/add_customer.html', {'form': form})


def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'rentals/add_product.html', {'form': form})

def add_rental(request):
    if request.method == 'POST':
        form = RentalForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rental_list')
    else:
        form = RentalForm()
    return render(request, 'rentals/add_rental.html', {'form': form})



def edit_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'rentals/edit_customer.html', {'form': form, 'customer': customer})
