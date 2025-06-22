from django.shortcuts import render, redirect, get_object_or_404
from .models import Rental, Customer, ProductAsset, ProductConfiguration, Payment
from .forms import CustomerForm, ProductAssetForm, ProductConfigurationForm, RentalForm
from django.db.models import Q
from django.db import IntegrityError
from django.contrib import messages
from django.utils.timezone import now
import uuid
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def homepage(request):
    return render(request, 'homepage.html')

@login_required
def rental_list(request):
    rentals = Rental.objects.filter(status='ongoing')
    return render(request, 'rentals/rental_list.html', {'rentals': rentals})

@login_required
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


@login_required
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


@login_required
def rental_history(request):
    query = request.GET.get('q', '')

    # Filter only completed rentals
    rentals = Rental.objects.filter(status='completed')

    # Search functionality
    if query:
        rentals = rentals.filter(
            Q(customer__name__icontains=query) |
            Q(asset__asset_id__icontains=query) |
            Q(asset__serial_no__icontains=query) |
            Q(asset__model_no__icontains=query) |
            Q(contract_number__icontains=query) |
            Q(made_by__icontains=query)|
            Q(payment__amount__icontains=query) |
            Q(payment__status__icontains=query)
        )

    rentals = rentals.order_by('-rental_start_date')
    # Add end_date for display
    for rental in rentals:
        rental.end_date = rental.rental_start_date + timedelta(days=rental.duration_days)

      # newest first

    return render(request, 'rentals/rental_history.html', {
        'rentals': rentals,
        'query': query
    })

@login_required
def add_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'rentals/add_customer.html', {'form': form})

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductAssetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductAssetForm()
    return render(request, 'rentals/add_product.html', {'form': form})


@login_required
def add_rental(request):
    if request.method == 'POST':
        form = RentalForm(request.POST)
        if form.is_valid():
            rental = form.save(commit=False)
            rental.status = 'ongoing'
            rental.save()

            # Create linked payment
            Payment.objects.create(
                rental=rental,
                amount=form.cleaned_data['payment_amount'],
                status=form.cleaned_data['payment_status']
            )

            return redirect('rental_list')
    else:
        form = RentalForm()
    return render(request, 'rentals/add_rental.html', {'form': form})

@login_required
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

@login_required
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


@login_required
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

@login_required    
def product_detail(request, pk):
    product = get_object_or_404(ProductAsset, pk=pk)
    configs = product.configurations.all().order_by('-date_of_config')
    return render(request, 'rentals/product_detail.html', {'product': product, 'configs': configs})


@login_required
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



@login_required
def delete_config(request, config_id):
    config = get_object_or_404(ProductConfiguration, pk=config_id)
    asset_id = config.asset.pk
    config.delete()
    return redirect('product_detail', pk=asset_id)


@login_required
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




@login_required
def rental_list(request):
    query = request.GET.get('q')
    filter_type = request.GET.get('filter')

    # Filter by status first
    if filter_type == 'ongoing':
        rentals = Rental.objects.filter(status='ongoing')
    elif filter_type == 'overdue':
        rentals = Rental.objects.filter(status='overdue')
    else:
        rentals = Rental.objects.filter(Q(status='ongoing') | Q(status='overdue'))

    # Then apply search filter on the already filtered queryset
    if query:
        rentals = rentals.filter(
            Q(customer__name__icontains=query) |
            Q(asset__asset_id__icontains=query) |
            Q(asset__serial_no__icontains=query)
        )

    # Sort and calculate due date
    rentals = rentals.order_by('-rental_start_date')
    for rental in rentals:
        rental.due_date = rental.rental_start_date + timedelta(days=rental.duration_days)

    return render(request, 'rentals/rental_list.html', {
        'rentals': rentals,
        'filter_type': filter_type
    })


@login_required
def mark_rental_completed(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id)
    rental.status = 'completed'
    rental.save()
    return redirect('rental_list')


@login_required
def edit_rental(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id)
    from datetime import timedelta
    rental.end_date = rental.rental_start_date + timedelta(days=rental.duration_days)

    if request.method == 'POST':
        form = RentalForm(request.POST, instance=rental)
        if form.is_valid():
            rental = form.save()
            # update or create the payment too
            payment_data = {
                'amount': form.cleaned_data['payment_amount'],
                'status': form.cleaned_data['payment_status'],
                'payment_method': form.cleaned_data['payment_method']
            }
            Payment.objects.update_or_create(rental=rental, defaults=payment_data)
            return redirect('rental_list')
    else:
        initial_data = {
        'payment_amount': rental.payment.amount if hasattr(rental, 'payment') else 0,
        'payment_status': rental.payment.status if hasattr(rental, 'payment') else 'pending',
        'payment_method': rental.payment.payment_method if hasattr(rental, 'payment') else 'cash',
        }
        form = RentalForm(instance=rental, initial=initial_data)

    return render(request, 'rentals/edit_rental.html', {'form': form,'rental': rental})
