from django.shortcuts import render, redirect, get_object_or_404
from .models import Rental, Customer, ProductAsset, ProductConfiguration
from .forms import CustomerForm, ProductAssetForm, ProductConfigurationForm, RentalForm
from django.db.models import Q
from django.db import IntegrityError
from django.contrib import messages
from django.utils.timezone import now
import uuid


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
    query = request.GET.get('q')
    sort_by = request.GET.get('sort', '-purchase_date')
    asset_type = request.GET.get('type')

    products = ProductAsset.objects.all()

    if query:
        products = products.filter(
            Q(asset_id__icontains=query) |
            Q(brand__icontains=query) |
            Q(model_no__icontains=query) |
            Q(serial_no__icontains=query)
        )

    if asset_type:
        products = products.filter(type_of_asset=asset_type)

    products = products.order_by(sort_by)

    asset_types = ProductAsset.objects.values_list('type_of_asset', flat=True).distinct()

    return render(request, 'rentals/product_list.html', {
        'products': products,
        'query': query,
        'sort_by': sort_by,
        'asset_type': asset_type,
        'asset_types': asset_types
    })


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
        form = ProductAssetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductAssetForm()
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


def edit_product(request, pk):
    asset = get_object_or_404(ProductAsset, pk=pk)
    if request.method == 'POST':
        form = ProductAssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductAssetForm(instance=asset)
    return render(request, 'rentals/edit_product.html', {'form': form, 'asset': asset})



def add_config(request, asset_id):
    asset = get_object_or_404(ProductAsset, pk=asset_id)

    if request.method == 'POST':
        form = ProductConfigurationForm(request.POST)
        if form.is_valid():
            config = form.save(commit=False)
            config.asset = asset  # Set the asset here!
            config.save()
            return redirect('product_detail', pk=asset.pk)
        else:
            print(form.errors)  # Optional: debug form issues
    else:
        form = ProductConfigurationForm()
        form.fields.pop('asset', None)  # Hide dropdown if still present

    return render(request, 'rentals/add_config.html', {'form': form, 'asset': asset})

    
def product_detail(request, pk):
    product = get_object_or_404(ProductAsset, pk=pk)
    configs = product.configurations.all().order_by('-date_of_config')
    return render(request, 'rentals/product_detail.html', {'product': product, 'configs': configs})



def edit_config(request, config_id):
    config = get_object_or_404(ProductConfiguration, pk=config_id)
    if request.method == 'POST':
        form = ProductConfigurationForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            return redirect('product_detail', pk=config.asset.pk)
    else:
        form = ProductConfigurationForm(instance=config)
    return render(request, 'rentals/edit_config.html', {'form': form, 'config': config})

def delete_config(request, config_id):
    config = get_object_or_404(ProductConfiguration, pk=config_id)
    asset_id = config.asset.pk
    config.delete()
    return redirect('product_detail', pk=asset_id)



import uuid
from django.utils.timezone import now

def clone_product(request, pk):
    original = get_object_or_404(ProductAsset, pk=pk)

    if request.method == 'POST':
        try:
            temp_serial = f"CLONE-{uuid.uuid4().hex[:8]}"
            new_asset = ProductAsset(
                type_of_asset=original.type_of_asset,
                brand=original.brand,
                model_no=original.model_no,
                serial_no=temp_serial,  # TEMP serial_no to pass uniqueness
                purchase_price=original.purchase_price,
                current_value=original.current_value,
                purchase_date=original.purchase_date,
                under_warranty=original.under_warranty,
                warranty_duration_months=original.warranty_duration_months,
                purchased_from=original.purchased_from,
            )
            new_asset.save()  # asset_id auto-generates here

            # Success: redirect to edit page so user can update serial_no
            messages.success(request, "Product cloned successfully. Please update serial number and save.")
            return redirect('edit_product', pk=new_asset.pk)

        except IntegrityError:
            messages.error(request, "Error: Could not clone product due to serial number conflict.")
            return redirect('product_list')

    return render(request, 'rentals/clone_confirm.html', {'product': original})
