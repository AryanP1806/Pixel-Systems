from django.shortcuts import render, redirect, get_object_or_404
from .models import Rental, Customer, ProductAsset, ProductConfiguration, Payment,Repair, PendingProduct, PendingCustomer, PendingRental, PendingProductConfiguration, Supplier, AssetType,CPUOption, HDDOption, RAMOption, DisplaySizeOption, GraphicsOption
from .forms import CustomerForm, ProductAssetForm, ProductConfigurationForm, RentalForm, PendingProductForm, PendingCustomerForm, PendingRentalForm, PendingProductConfigurationForm, SupplierForm, RepairForm, AssetTypeForm,CPUOptionForm,  HDDOptionForm, RAMOptionForm, DisplaySizeOptionForm, GraphicsOptionForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from django.db import IntegrityError
from django.contrib import messages
from django.utils.timezone import now
from django.utils.dateparse import parse_date
import uuid
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from datetime import datetime
import json
from collections import defaultdict

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def homepage(request):
    return render(request, 'homepage.html')

@login_required
def rental_list(request):
    rentals = Rental.objects.filter(status__in=['ongoing'])
    return render(request, 'rentals/rental_list.html', {'rentals': rentals})

@login_required
def sold_assets(request):
    products = ProductAsset.objects.filter(condition_status='sold').order_by('-sale_date')
    return render(request, 'rentals/sold_assets.html', {'products': products})

def settings_page(request):
    return render(request, 'settings.html')



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
    sort_by = request.GET.get('sort', 'asset_id')
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



def asset_type_list(request):
    asset_types = AssetType.objects.all()
    return render(request, 'products/asset_type_list.html', {'asset_types': asset_types})

def add_asset_type(request):
    form = AssetTypeForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('asset_type_list')
    return render(request, 'products/add_asset_type.html', {'form': form})

def edit_asset_type(request, pk):
    asset_type = get_object_or_404(AssetType, pk=pk)
    form = AssetTypeForm(request.POST or None, instance=asset_type)
    if form.is_valid():
        form.save()
        return redirect('asset_type_list')
    return render(request, 'products/edit_asset_type.html', {'form': form})



@login_required
@user_passes_test(lambda u: u.is_superuser)
def approval_dashboard(request):
    pending_products = PendingProduct.objects.all()
    pending_customers = PendingCustomer.objects.all()
    pending_rentals = PendingRental.objects.all()
    pending_configs = PendingProductConfiguration.objects.all()

    return render(request, 'rentals/approval_dashboard.html', {
        'pending_products': pending_products,
        'pending_customers': pending_customers,
        'pending_rentals': pending_rentals,
        'pending_configs': pending_configs,
    })



@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_config(request, pk):
    pending = get_object_or_404(PendingProductConfiguration, pk=pk)
    config = ProductConfiguration.objects.create(
        asset=pending.asset,
        date_of_config=pending.date_of_config,
        cpu=pending.cpu,
        ram=pending.ram,
        hdd=pending.hdd,
        ssd=pending.ssd,
        graphics=pending.graphics,
        display_size=pending.display_size,
        power_supply=pending.power_supply,
        detailed_config=pending.detailed_config,
        edited_by=pending.submitted_by
    )

    # if config.repair_cost and config.repair_cost > 0:
    #     Repair.objects.create(
    #         product=config.asset,
    #         date=config.date_of_config,
    #         cost=config.repair_cost,
    #         description="From approved config",
    #         edited_by=request.user
    #     )
    pending.delete()
    return redirect('approval_dashboard')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_config(request, pk):
    pending = get_object_or_404(PendingProductConfiguration, pk=pk)
    pending.delete()
    return redirect('approval_dashboard')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_product(request, pk):
    pending = get_object_or_404(PendingProduct, pk=pk)

    real_product = ProductAsset.objects.create(
        type_of_asset=pending.type_of_asset,
        brand=pending.brand,
        model_no=pending.model_no,
        serial_no=pending.serial_no,
        purchase_price=pending.purchase_price,
        current_value=pending.current_value,
        purchase_date=pending.purchase_date,
        under_warranty=pending.under_warranty,
        warranty_duration_months=pending.warranty_duration_months,
        purchased_from=pending.purchased_from,
        condition_status=pending.condition_status,
        edited_by=pending.submitted_by
    )

    pending.delete()
    return redirect('approval_dashboard')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_product(request, pk):
    get_object_or_404(PendingProduct, pk=pk).delete()
    return redirect('approval_dashboard')


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
            Q(edited_by__username__icontains=query)|
            Q(payment__amount__icontains=query) |
            Q(payment__status__icontains=query)
        )

    rentals = rentals.order_by('-rental_start_date')
    # Add end_date for display
    # for rental in rentals:
    #     rental.end_date = rental.rental_start_date + timedelta(days=rental.duration_days)

      # newest first

    return render(request, 'rentals/rental_history.html', {
        'rentals': rentals,
        'query': query
    })


@login_required
def add_customer(request):
    if request.method == 'POST':
        if request.user.is_superuser:
            form = CustomerForm(request.POST)
            if form.is_valid():
                customer = form.save(commit=False)
                customer.edited_by = request.user
                customer.save()
                return redirect('customer_list')
        else:
            form = PendingCustomerForm(request.POST)
            if form.is_valid():
                pending = form.save(commit=False)
                pending.submitted_by = request.user
                pending.save()
                return redirect('customer_list')
    else:
        form = CustomerForm() if request.user.is_superuser else PendingCustomerForm()

    return render(request, 'rentals/add_customer.html', {'form': form})





# @login_required
# def add_product(request):
#     if request.method == 'POST':
#         if request.user.is_superuser:
#             form = ProductAssetForm(request.POST)
#             if form.is_valid():
#                 product = form.save(commit=False)
#                 product.edited_by = request.user
#                 product.save()
#                 return redirect('product_list')
#         else:
#             form = PendingProductForm(request.POST)
#             if form.is_valid():
#                 pending = form.save(commit=False)
#                 pending.submitted_by = request.user
#                 pending.save()
#                 return redirect('product_list')
#     else:
#         form = ProductAssetForm() if request.user.is_superuser else PendingProductForm()

#     return render(request, 'rentals/add_product.html', {'form': form})
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ProductAssetForm, PendingProductForm
from .models import ProductAsset, PendingProduct

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductAssetForm(request.POST)
        if form.is_valid():
            if request.user.is_superuser:
                product = form.save(commit=False)
                product.edited_by = request.user
                product.save()
                return redirect('product_list')
            
                
            else:
                # Create a PendingProduct instance from cleaned_data
                pending = PendingProduct(
                    type_of_asset=form.cleaned_data['type_of_asset'],
                    brand=form.cleaned_data['brand'],
                    model_no=form.cleaned_data['model_no'],
                    serial_no=form.cleaned_data['serial_no'],
                    purchase_price=form.cleaned_data['purchase_price'],
                    current_value=form.cleaned_data['current_value'],
                    purchase_date=form.cleaned_data['purchase_date'],
                    under_warranty=form.cleaned_data['under_warranty'],
                    warranty_duration_months=form.cleaned_data['warranty_duration_months'],
                    purchased_from=form.cleaned_data['purchased_from'],
                    condition_status=form.cleaned_data['condition_status'],
                    hsn_code=form.cleaned_data.get('hsn_code'),
                    asset_number=form.cleaned_data.get('asset_number'),
                    asset_id=form.cleaned_data.get('asset_id'),
                    sold_to=form.cleaned_data.get('sold_to'),
                    sale_price=form.cleaned_data.get('sale_price'),
                    sale_date=form.cleaned_data.get('sale_date'),
                    date_marked_dead=form.cleaned_data.get('date_marked_dead'),
                    damage_narration=form.cleaned_data.get('damage_narration'),
                    submitted_by=request.user  # ✅ Automatically assign
                )
                try:
                    pending.save()
                except Exception as e:
                    print("Pending product save error:", e)

                return redirect('product_list')
    
        else:
            return render(request, 'rentals/add_product.html', {'form': form})  
    else:
        form = ProductAssetForm()

    return render(request, 'rentals/add_product.html', {'form': form})


            


@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_customer(request, pk):
    pending = get_object_or_404(PendingCustomer, pk=pk)
    Customer.objects.create(
        name=pending.name,
        email=pending.email,
        phone_number_primary=pending.phone_number_primary,
        phone_number_secondary=pending.phone_number_secondary,
        address_primary=pending.address_primary,
        address_secondary=pending.address_secondary,
        is_permanent=pending.is_permanent,
        is_bni_member=pending.is_bni_member,
        edited_by=pending.submitted_by
    )
    pending.delete()
    return redirect('approval_dashboard')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_customer(request, pk):
    get_object_or_404(PendingCustomer, pk=pk).delete()
    return redirect('approval_dashboard')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import RentalForm, PendingRentalForm
from .models import Rental, Payment

@login_required
def add_rental(request):
    if request.method == 'POST':
        if request.user.is_superuser:
            form = RentalForm(request.POST)
            if form.is_valid():
                rental = form.save(commit=False)
                rental.edited_by = request.user
                rental.save()

                # Create associated payment
                Payment.objects.create(
                    rental=rental,
                    amount=form.cleaned_data['payment_amount'],
                    status=form.cleaned_data['payment_status'],
                    payment_method=form.cleaned_data['payment_method'],
                    edited_by=request.user
                )
                return redirect('rental_list')
        else:
            form = PendingRentalForm(request.POST)
            if form.is_valid():
                pending = form.save(commit=False)
                pending.submitted_by = request.user

                # ✅ Copy payment and edited_by manually
                pending.payment_amount = form.cleaned_data.get('payment_amount')
                pending.edited_by = request.user
                pending.save()
                return redirect('rental_list')
    else:
        form = RentalForm() if request.user.is_superuser else PendingRentalForm()

    return render(request, 'rentals/add_rental.html', {'form': form})




@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_rental(request, pk):
    pending = get_object_or_404(PendingRental, pk=pk)
    rental = Rental.objects.create(
    customer=pending.customer,
    asset=pending.asset,
    rental_start_date=pending.rental_start_date,
    # duration_days=pending.duration_days,
    contract_number=pending.contract_number,
    status=pending.status,
    edited_by=pending.edited_by
    )
    Payment.objects.create(
    rental=rental,
    amount=pending.payment_amount,
    status='pending',  # Or whatever was stored
    payment_method='cash',  # Optional: add more fields to PendingRental
    edited_by=pending.edited_by
    )
    pending.delete()
    return redirect('approval_dashboard')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_rental(request, pk):
    get_object_or_404(PendingRental, pk=pk).delete()
    return redirect('approval_dashboard')



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
            product = form.save(commit=False)
            product.edited_by = request.user
            form.save()
            return redirect('product_list')
    else:
        form = ProductAssetForm(instance=asset)
    return render(request, 'rentals/edit_product.html', {'form': form, 'asset': asset})

# @login_required
# def add_config(request, pk):
#     asset = get_object_or_404(ProductAsset, pk=pk)

#     if request.method == 'POST':
#         form = ProductConfigurationForm(request.POST)
#         if form.is_valid():
#             if request.user.is_superuser:
#                 config = form.save(commit=False)
#                 config.asset = asset
#                 config.edited_by = request.user
#                 config.save()
#             else:
#                 pending_config = PendingProductConfiguration(
#                     asset=asset,
#                     date_of_config=form.cleaned_data['date_of_config'],
#                     ram=form.cleaned_data['ram'],
#                     hdd=form.cleaned_data['hdd'],
#                     ssd=form.cleaned_data['ssd'],
#                     graphics=form.cleaned_data['graphics'],
#                     display_size=form.cleaned_data['display_size'],
#                     power_supply=form.cleaned_data['power_supply'],
#                     detailed_config=form.cleaned_data['detailed_config'],
#                     submitted_by=request.user
#                 )
#                 pending_config.save()
#             return redirect('product_detail', pk=pk)
#     else:
#         form = ProductConfigurationForm(initial={'asset': asset})

#     return render(request, 'rentals/add_config.html', {'form': form, 'asset': asset})


from .models import ProductAsset, ProductConfiguration
from .forms import ProductConfigurationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

@login_required
def add_config(request, pk):
    asset = get_object_or_404(ProductAsset, pk=pk)

    # Try to get the latest configuration for pre-filling
    last_config = asset.configurations.order_by('-date_of_config').first()

    if request.method == 'POST':
        form = ProductConfigurationForm(request.POST)
        if form.is_valid():
            if request.user.is_superuser:
                config = form.save(commit=False)
                config.asset = asset
                config.edited_by = request.user
                config.save()
                return redirect('product_detail', pk=pk)
            else:
                # Handle non-superuser submission to PendingProductConfiguration
                from .models import PendingProductConfiguration
                pending = PendingProductConfiguration(
                    asset=asset,
                    date_of_config=form.cleaned_data['date_of_config'],
                    cpu=form.cleaned_data.get('cpu'),
                    ram=form.cleaned_data.get('ram'),
                    hdd=form.cleaned_data.get('hdd'),
                    ssd=form.cleaned_data.get('ssd'),
                    graphics=form.cleaned_data.get('graphics'),
                    display_size=form.cleaned_data.get('display_size'),
                    power_supply=form.cleaned_data.get('power_supply'),
                    detailed_config=form.cleaned_data.get('detailed_config'),
                    submitted_by=request.user
                )
                pending.save()
                return redirect('product_detail', pk=pk)
    else:
        if last_config:
            # Prefill with last config
            form = ProductConfigurationForm(initial={
                'cpu': last_config.cpu,
                'ram': last_config.ram,
                'hdd': last_config.hdd,
                'ssd': last_config.ssd,
                'graphics': last_config.graphics,
                'display_size': last_config.display_size,
                'power_supply': last_config.power_supply,
                'detailed_config': last_config.detailed_config,
                
            })
        else:
            # First config: blank form
            form = ProductConfigurationForm()

    return render(request, 'rentals/add_config.html', {'form': form, 'asset': asset})

@login_required    
def product_detail(request, pk):
    product = get_object_or_404(ProductAsset, pk=pk)
    configs = product.configurations.all().order_by('-date_of_config')
    repairs = product.repairs.all().order_by('-date')
    return render(request, 'rentals/product_detail.html', {
        'product': product,
        'configs': configs,
        'repairs': repairs
        })


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

    # if request.method == 'POST':

    if request.user.is_superuser:
    # Create and save immediately
        new_product = ProductAsset(
            type_of_asset=original.type_of_asset,
            brand=original.brand,
            model_no=original.model_no,
            serial_no=f"Clone-{timezone.now().year}-{ProductAsset.objects.count()+1}",
            purchase_price=original.purchase_price,
            current_value=original.current_value,
            purchase_date=original.purchase_date,
            under_warranty=original.under_warranty,
            warranty_duration_months=original.warranty_duration_months,
            purchased_from=original.purchased_from,
            condition_status=original.condition_status,
            edited_by=request.user
        )
        new_product.save()  # This will auto-generate asset_id
        messages.success(request, "Product cloned successfully. Please update serial number and save.")
        return redirect('edit_product', pk=new_product.pk)
    else:
        # Save to pending approval
        new_product = PendingProduct(
            type_of_asset=original.type_of_asset,
            brand=original.brand,
            model_no=original.model_no,
            serial_no=f"Clone-{timezone.now().year}",
            purchase_price=original.purchase_price,
            current_value=original.current_value,
            purchase_date=original.purchase_date,
            under_warranty=original.under_warranty,
            warranty_duration_months=original.warranty_duration_months,
            purchased_from=original.purchased_from,
            condition_status=original.condition_status,
            submitted_by=request.user
        )
        new_product.save()  # This will auto-generate asset_id
        messages.success(request, "Product cloned successfully. Please update serial number and save.")
        return redirect('edit_product', pk=new_product.pk)
   

    



@login_required
def rental_list(request):
    query = request.GET.get('q')
    filter_type = request.GET.get('filter')

    # Filter by status first
    # if filter_type == 'ongoing':
    rentals = Rental.objects.filter(status='ongoing')
    # elif filter_type == 'overdue':
    #     rentals = Rental.objects.filter(status='overdue')
    # else:
    #     rentals = Rental.objects.filter(Q(status='ongoing') | Q(status='overdue'))

    # Then apply search filter on the already filtered queryset
    if query:
        rentals = rentals.filter(
            Q(customer__name__icontains=query) |
            Q(asset__asset_id__icontains=query) |
            Q(asset__serial_no__icontains=query)
        )

    # Sort and calculate due date
    rentals = rentals.order_by('-rental_start_date')
    # for rental in rentals:
    #     rental.due_date = rental.rental_start_date + timedelta(days=rental.duration_days)

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
    # rental.end_date = rental.rental_start_date + timedelta(days=rental.duration_days)

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



# @login_required
# def check_overdue_view(request):
#     today = timezone.now().date()
#     rentals = Rental.objects.filter(status='ongoing')

#     for rental in rentals:
#         due_date = rental.rental_start_date + timedelta(days=rental.duration_days)
#         days_left = (due_date - today).days

#         # Overdue: send overdue email
#         if due_date < today:
#             rental.status = 'overdue'
#             rental.save()

#             send_mail(
#                 subject='🔴 Rental Overdue Notification',
#                 message=f'Rental for {rental.customer.name} is overdue.\nAsset ID: {rental.asset.asset_id}',
#                 from_email='aryanpore3056@gmail.com',
#                 recipient_list=['aryanpore3056@gmail.com'],
#                 fail_silently=False,
#             )





@login_required
def report_dashboard(request):
    customers = Customer.objects.all()
    products = ProductAsset.objects.all()

    customer_id = request.GET.get('customer')
    product_id = request.GET.get('product')
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')

  # rentals = Rental.objects.filter(status='completed')
    rentals = Rental.objects.select_related('payment').all()

    product_obj = None
    if product_id:
        try:
            product_obj = ProductAsset.objects.get(id=product_id)
        except ProductAsset.DoesNotExist:
            product_obj = None

    gross_profit = maintenance_cost = net_profit = None
    if product_obj:
        gross_profit = float(product_obj.total_rent_earned or 0)
        if product_obj.condition_status=='sold' and product_obj.sale_price:
            gross_profit += float(product_obj.sale_price)
        maintenance_cost = float(product_obj.total_repairs or 0)
        net_profit = gross_profit - maintenance_cost



    if customer_id:
        rentals = rentals.filter(customer_id=customer_id)
    if product_id:
        rentals = rentals.filter(asset_id=product_id)
    if start:
        rentals = rentals.filter(rental_start_date__gte=parse_date(start))
    if end:
        rentals = rentals.filter(rental_start_date__lte=parse_date(end))

    total_revenue = sum(r.payment.amount for r in rentals if hasattr(r, 'payment'))
    total_rentals = rentals.count()
    # total_days = sum(r.duration_days or 0 for r in rentals)

    # Monthly revenue data
    monthly = {}
    for r in rentals:
        if hasattr(r, 'payment'):
            month = r.rental_start_date.strftime("%Y-%m")
            monthly[month] = monthly.get(month, 0) + r.payment.amount



    top_assets = (
        ProductAsset.objects.annotate(total_income=Sum('rentals__payment__amount'))
        .filter(total_income__gt=0)
        .order_by('-total_income')[:5]  # Top 5 assets
    )



    type_revenue = defaultdict(float)
    for asset in ProductAsset.objects.prefetch_related('rentals__payment'):
        asset_type = asset.type_of_asset
        total_income = sum(r.payment.amount for r in asset.rentals.all() if r.payment)
        type_revenue[asset_type] += float(total_income)

    type_data = rentals.filter(payment__isnull=False).values('asset__type_of_asset__name').annotate(
        total=Sum('payment__amount')
    ).order_by('-total')

    type_labels = [entry['asset__type_of_asset__name'] for entry in type_data]
    type_values = [float(entry['total']) for entry in type_data if entry['total']]



    customer_revenue = {}
    for customer in Customer.objects.all():
        total = Rental.objects.filter(customer=customer, payment__isnull=False).aggregate(total=Sum('payment__amount'))['total']
        if total:
            customer_revenue[customer.name] = float(total)

    sorted_customers = sorted(customer_revenue.items(), key=lambda x: x[1], reverse=True)
    customer_labels = [name for name, _ in sorted_customers]
    customer_values = [value for _, value in sorted_customers]

    context = {
        'customers': customers,
        'products': products,
        'rentals': rentals,
        'total_revenue': total_revenue,
        'total_rentals': total_rentals,

        'gross_profit': gross_profit,
        'maintenance_cost': maintenance_cost,
        'net_profit': net_profit,
        'product_obj': product_obj, 
        'product_id': product_id,
        'gross_profit': gross_profit,
        'maintenance_cost': maintenance_cost,
        'net_profit': net_profit,
        'monthly_labels': json.dumps(list(reversed(monthly.keys()))),
        'monthly_values': json.dumps([float(v) for v in reversed(monthly.values())]),
        'top_assets': top_assets,
        'type_labels': json.dumps(type_labels),
        'type_values': json.dumps(type_values),
        'customer_labels': json.dumps(customer_labels),
        'customer_values': json.dumps(customer_values),

    }
    return render(request, 'rentals/report_dashboard.html', context)





@login_required
def supplier_list(request):
    query = request.GET.get('q', '')
    suppliers = Supplier.objects.all()
    if query:
        suppliers = suppliers.filter(
            Q(name__icontains=query) |
            Q(gstin__icontains=query) |
            Q(phone_primary__icontains=query) |
            Q(phone_secondary__icontains=query) |
            Q(email__icontains=query) |
            Q(reference_name__icontains=query)
        )

    return render(request, 'rentals/supplier_list.html', {
        'suppliers': suppliers,
        'query': query
    })


@login_required
def add_supplier(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'rentals/add_supplier.html', {'form': form})


@login_required
def edit_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'rentals/edit_supplier.html', {'form': form, 'supplier': supplier})


@login_required
def send_billing_reminder(request):
    today = now().day
    print("Today's date:", today)
    rentals_due_today = Rental.objects.filter(billing_day=today, status='ongoing')

    if not rentals_due_today.exists():
        messages.info(request, "No rentals due for billing today.")
        return redirect('rental_list')

    body_lines = []
    for rental in rentals_due_today:
        asset_id = rental.asset.asset_id if rental.asset else 'Unknown'
        customer_name = rental.customer.name if rental.customer else 'Unknown Customer'
        body_lines.append(f"- Asset: {asset_id} | Customer: {customer_name}")

    body = "Billing Reminder for Today:\n\n" + "\n".join(body_lines)

    try:
        send_mail(
            subject="Todays Billing Reminder",
            message=body,
            from_email='aryanpore3056@gmail.com',
            recipient_list=['aryanpore3056@gmail.com'],
            fail_silently=False,
            )
        messages.success(request, "Billing reminder sent successfully!")
    except Exception as e:
        messages.error(request, f"Failed to send reminder: {e}")


    return redirect('rental_list')



# @login_required
# def add_repair(request):
#     if request.method == 'POST':
#         form = RepairForm(request.POST)
#         if form.is_valid():
#             repair = form.save(commit=False)
#             repair.edited_by = request.user
#             repair.save()
#             return redirect('product_list')  # or wherever you want to go after adding
#     else:
#         form = RepairForm()
    
#     return render(request, 'rentals/add_repair.html', {'form': form})


@login_required
def add_repair(request, pk=None):
    product = None
    if pk:
        product = get_object_or_404(ProductAsset, pk=pk)

    if request.method == 'POST':
        form = RepairForm(request.POST)
        if form.is_valid():
            repair = form.save(commit=False)
            repair.edited_by = request.user
            form_product = form.cleaned_data.get("product")
            if not form_product and product:
                repair.product = product
            repair.save()
            return redirect('product_detail', pk=repair.product.pk)
    else:
        form = RepairForm(initial={'product': product} if product else None)
        if product:
            form.fields['product'].queryset = ProductAsset.objects.filter(id=product.id)
            form.fields['product'].widget.attrs['readonly'] = True  # optional disable

    return render(request, 'rentals/add_repair.html', {'form': form})


def settings_home(request):
    return render(request, 'rentals/settings.html')



def manage_hdd_Options(request):
    items = HDDOption.objects.all()
    editing = False
    instance = None

    if request.GET.get("edit"):
        instance = get_object_or_404(HDDOption, id=request.GET["edit"])
        editing = True

    form = HDDOptionForm(request.POST or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('manage_hdd_Options')

    return render(request, 'rentals/manage_Options.html', {
        'form': form,
        'items': items,
        'field_name': 'HDD',
        'title': 'HDD',
        'editing': editing,
        'current_view': 'manage_hdd_Options',
    })

def manage_ram_Options(request):
    items = RAMOption.objects.all()
    editing = False
    instance = None

    if request.GET.get("edit"):
        instance = get_object_or_404(RAMOption, id=request.GET["edit"])
        editing = True

    form = RAMOptionForm(request.POST or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('manage_ram_Options')

    return render(request, 'rentals/manage_Options.html', {
        'form': form,
        'items': items,
        'field_name': 'RAM',
        'title': 'RAM',
        'editing': editing,
        'current_view': 'manage_ram_Options',
    })


def manage_cpu_Options(request):
    items = CPUOption.objects.all()
    editing = False
    instance = None

    if request.GET.get("edit"):
        instance = get_object_or_404(CPUOption, id=request.GET["edit"])
        editing = True

    form = CPUOptionForm(request.POST or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('manage_cpu_Options')

    return render(request, 'rentals/manage_Options.html', {
        'form': form,
        'items': items,
        'field_name': 'CPU',
        'title': 'CPU',
        'editing': editing,
        'current_view': 'manage_cpu_Options',
    })


def manage_display_size_Options(request):
    items = DisplaySizeOption.objects.all()
    editing = False
    instance = None

    if request.GET.get("edit"):
        instance = get_object_or_404(DisplaySizeOption, id=request.GET["edit"])
        editing = True

    form = DisplaySizeOptionForm(request.POST or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('manage_display_size_Options')

    return render(request, 'rentals/manage_Options.html', {
        'form': form,
        'items': items,
        'field_name': 'Display Size',
        'title': 'Display Size',
        'editing': editing,
        'current_view': 'manage_display_size_Options',
    })


def manage_graphics_Options(request):
    items =GraphicsOption.objects.all()
    editing = False
    instance = None

    if request.GET.get("edit"):
        instance = get_object_or_404(GraphicsOption, id=request.GET["edit"])
        editing = True

    form = GraphicsOptionForm(request.POST or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('manage_graphics_Options')

    return render(request, 'rentals/manage_Options.html', {
        'form': form,
        'items': items,
        'field_name': 'Graphics',
        'title': 'Graphics',
        'editing': editing,
        'current_view': 'manage_graphics_Options',
    })