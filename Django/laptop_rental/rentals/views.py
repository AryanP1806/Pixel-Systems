from django.shortcuts import render, redirect, get_object_or_404
from .models import Rental, Customer, ProductAsset, ProductConfiguration, Payment,Repair, PendingProduct, PendingCustomer, PendingRental, PendingProductConfiguration, Supplier, AssetType,CPUOption, HDDOption, RAMOption, DisplaySizeOption, GraphicsOption, PendingRepair
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
def approval_dashboard(request):
    pending_products = PendingProduct.objects.all()
    pending_customers = PendingCustomer.objects.all()
    pending_rentals = PendingRental.objects.all()
    pending_configs = PendingProductConfiguration.objects.all()


    products_data = [
        {"pending": p, "old": p.original_product} for p in pending_products
    ]
    customers_data = [
        {"pending": pc, "old": pc.original_customer} for pc in pending_customers
    ]
    rentals_data = [
        {"pending": pr, "old": pr.original_rental} for pr in pending_rentals
    ]
    configs_data = [
        {"pending": cfg, "old": cfg.original_config} for cfg in pending_configs
    ]
    
    return render(request, "rentals/approval_dashboard.html", {
        "pending_products": products_data,
        "pending_customers": customers_data,
        "pending_rentals": rentals_data,
        "pending_configs": configs_data,
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
    if pending.pending_type == 'edit' and pending.original_product:
        product = pending.original_product
        # copy fields
        for field in [
            'type_of_asset', 'brand', 'model_no', 'serial_no', 'purchase_price', 'current_value',
            'purchase_date', 'under_warranty', 'warranty_duration_months', 'purchased_from',
            'condition_status', 'asset_number', 'asset_id', 'hsn_code', 'sold_to', 'sale_price',
            'sale_date', 'date_marked_dead', 'damage_narration']:
            setattr(product, field, getattr(pending, field))
        product.save()
    else:
        ProductAsset.objects.create(
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
            asset_number=pending.asset_number,
            asset_id=pending.asset_id,
            hsn_code=pending.hsn_code,
            sold_to=pending.sold_to,
            sale_price=pending.sale_price,
            sale_date=pending.sale_date,
            date_marked_dead=pending.date_marked_dead,
            damage_narration=pending.damage_narration,
            edited_by=pending.submitted_by
        )
    pending.delete()
    messages.success(request, "Approved successfully.")
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

    if pending.original_customer:
        customer = pending.original_customer
        customer.name = pending.name
        customer.email = pending.email
        customer.phone_number_primary = pending.phone_number_primary
        customer.phone_number_secondary = pending.phone_number_secondary
        customer.address_primary = pending.address_primary
        customer.address_secondary = pending.address_secondary
        customer.is_permanent = pending.is_permanent
        customer.is_bni_member = pending.is_bni_member
        customer.reference_name = pending.reference_name
        customer.edited_by = pending.submitted_by
        customer.save()
    else:
        Customer.objects.create(
            name=pending.name,
            email=pending.email,
            phone_number_primary=pending.phone_number_primary,
            phone_number_secondary=pending.phone_number_secondary,
            address_primary=pending.address_primary,
            address_secondary=pending.address_secondary,
            is_permanent=pending.is_permanent,
            is_bni_member=pending.is_bni_member,
            reference_name=pending.reference_name,
            edited_by=pending.submitted_by,
        )

    pending.delete()
    messages.success(request, "Customer approved successfully.")
    return redirect("approval_dashboard")

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

    if pending.original_rental:
        rental = pending.original_rental
        rental.customer = pending.customer
        rental.asset = pending.asset
        rental.rental_start_date = pending.rental_start_date
        rental.rental_end_date = pending.rental_end_date
        rental.billing_day = pending.billing_day
        rental.contract_number = pending.contract_number
        rental.contract_validity = pending.contract_validity
        rental.status = pending.status
        rental.edited_by = pending.submitted_by
        rental.save()

        Payment.objects.update_or_create(
            rental=rental,
            defaults={
                "amount": pending.payment_amount,
                "status": "pending",
                "payment_method": "cash",

                "edited_by": pending.submitted_by,
            },
        )
    else:
        rental = Rental.objects.create(
            customer=pending.customer,
            asset=pending.asset,
            rental_start_date=pending.rental_start_date,
            rental_end_date=pending.rental_end_date,
            billing_day=pending.billing_day,
            contract_number=pending.contract_number,
            contract_validity=pending.contract_validity,
            status=pending.status,
            edited_by=pending.submitted_by,
        )

        Payment.objects.create(
            rental=rental,
            amount=pending.payment_amount,
            status="pending",
            payment_method="cash",
            edited_by=pending.submitted_by,
        )

    pending.delete()
    messages.success(request, "Rental approved successfully.")
    return redirect("approval_dashboard")

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_rental(request, pk):
    get_object_or_404(PendingRental, pk=pk).delete()
    return redirect('approval_dashboard')



@login_required
def edit_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.user.is_superuser:
        form = CustomerForm(request.POST or None, instance=customer)
        if request.method == "POST" and form.is_valid():
            updated_customer = form.save(commit=False)
            updated_customer.edited_by = request.user
            updated_customer.save()
            messages.success(request, "Customer updated successfully.")
            return redirect("customer_list")
    else:
        if request.method == "POST":
            form = CustomerForm(request.POST, instance=customer)
            if form.is_valid():
                cleaned = form.cleaned_data
                pending = PendingCustomer(
                    original_customer=customer,  # ✅ Link original customer
                    name=cleaned["name"],
                    email=cleaned["email"],
                    phone_number_primary=cleaned["phone_number_primary"],
                    phone_number_secondary=cleaned.get("phone_number_secondary"),
                    address_primary=cleaned["address_primary"],
                    address_secondary=cleaned.get("address_secondary"),
                    is_permanent=cleaned.get("is_permanent", False),
                    is_bni_member=cleaned.get("is_bni_member", False),
                    reference_name=cleaned.get("reference_name"),
                    submitted_by=request.user,
                )
                pending.save()
                messages.success(request, "Customer changes submitted for approval.")
                return redirect("customer_list")
        else:
            form = CustomerForm(instance=customer)

    return render(request, "rentals/edit_customer.html", {"form": form, "customer": customer})


@login_required
def edit_product(request, pk):
    product = get_object_or_404(ProductAsset, pk=pk)
    if request.user.is_superuser:
        form = ProductAssetForm(request.POST or None, instance=product)
        if request.method == 'POST' and form.is_valid():
            product = form.save(commit=False)
            product.edited_by = request.user
            product.save()
            return redirect('product_list')
    else:
        if request.method == 'POST':
            form = ProductAssetForm(request.POST, instance=product)
            if form.is_valid():
                cleaned = form.cleaned_data
                pending = PendingProduct(
                    original_product=product,
                    pending_type='edit',
                    submitted_by=request.user,
                    type_of_asset=cleaned['type_of_asset'],
                    brand=cleaned['brand'],
                    model_no=cleaned['model_no'],
                    serial_no=cleaned['serial_no'],
                    purchase_price=cleaned['purchase_price'],
                    current_value=cleaned['current_value'],
                    purchase_date=cleaned['purchase_date'],
                    under_warranty=cleaned['under_warranty'],
                    warranty_duration_months=cleaned['warranty_duration_months'],
                    purchased_from=cleaned['purchased_from'],
                    condition_status=cleaned['condition_status'],
                    asset_number=cleaned.get('asset_number'),
                    asset_id=cleaned.get('asset_id'),
                    hsn_code=cleaned.get('hsn_code'),
                    sold_to=cleaned.get('sold_to'),
                    sale_price=cleaned.get('sale_price'),
                    sale_date=cleaned.get('sale_date'),
                    date_marked_dead=cleaned.get('date_marked_dead'),
                    damage_narration=cleaned.get('damage_narration'),
                )
                pending.save()
                messages.success(request, "Changes submitted for approval.")
                return redirect('product_list')
        else:
            form = ProductAssetForm(instance=product)
    return render(request, 'rentals/edit_product.html', {'form': form, 'product': product})



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
def edit_config(request, pk):
    config = get_object_or_404(ProductConfiguration, pk=pk)

    if request.user.is_superuser:
        # Superusers can directly edit
        form = ProductConfigurationForm(request.POST or None, instance=config)
        if request.method == "POST" and form.is_valid():
            updated_config = form.save(commit=False)
            updated_config.edited_by = request.user
            updated_config.save()
            messages.success(request, "Configuration updated successfully.")
            return redirect("config_list")
    else:
        # Normal users → Create a pending config
        if request.method == "POST":
            form = ProductConfigurationForm(request.POST, instance=config)
            if form.is_valid():
                cleaned = form.cleaned_data

                # ✅ Ensure date_of_config is always set
                date_value = cleaned.get("date_of_config") or config.date_of_config or now().date()

                PendingProductConfiguration.objects.create(
                    asset=config.asset,
                    date_of_config=date_value,
                    cpu=cleaned.get("cpu"),
                    ram=cleaned.get("ram"),
                    hdd=cleaned.get("hdd"),
                    ssd=cleaned.get("ssd"),
                    graphics=cleaned.get("graphics"),
                    display_size=cleaned.get("display_size"),
                    power_supply=cleaned.get("power_supply"),
                    detailed_config=cleaned.get("detailed_config"),
                    submitted_by=request.user,
                    is_edit=True,
                    original_config=config,
                )
                messages.success(request, "Configuration changes submitted for approval.")
                return redirect("config_list")
        else:
            form = ProductConfigurationForm(instance=config)

    return render(request, "rentals/edit_config.html", {"form": form, "config": config})



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

    if request.user.is_superuser:
        initial_data = {
            "payment_amount": rental.payment.amount if hasattr(rental, "payment") else 0,
            "payment_status": rental.payment.status if hasattr(rental, "payment") else "pending",
            "payment_method": rental.payment.payment_method if hasattr(rental, "payment") else "cash",
        }
        form = RentalForm(request.POST or None, instance=rental, initial=initial_data)
        if request.method == "POST" and form.is_valid():
            updated_rental = form.save(commit=False)
            updated_rental.edited_by = request.user
            updated_rental.save()

            Payment.objects.update_or_create(
                rental=updated_rental,
                defaults={
                    "amount": form.cleaned_data["payment_amount"],
                    "status": form.cleaned_data["payment_status"],
                    "payment_method": form.cleaned_data["payment_method"],
                    "edited_by": request.user,
                },
            )
            messages.success(request, "Rental updated successfully.")
            return redirect("rental_list")
    else:
        if request.method == "POST":
            form = RentalForm(request.POST, instance=rental)
            if form.is_valid():
                cleaned = form.cleaned_data
                pending = PendingRental(
                    original_rental=rental,  # ✅ Link original rental
                    customer=cleaned["customer"],
                    asset=cleaned["asset"],
                    rental_start_date=cleaned["rental_start_date"],
                    rental_end_date=cleaned["rental_end_date"],
                    billing_day=cleaned.get("billing_day"),
                    contract_number=cleaned.get("contract_number"),
                    contract_validity=cleaned.get("contract_validity"),
                    status=cleaned.get("status"),
                    payment_amount=cleaned.get("payment_amount"),
                    edited_by=request.user,
                    submitted_by=request.user,
                )
                pending.save()
                messages.success(request, "Rental changes submitted for approval.")
                return redirect("rental_list")
        else:
            initial_data = {
                "payment_amount": rental.payment.amount if hasattr(rental, "payment") else 0,
                "payment_status": rental.payment.status if hasattr(rental, "payment") else "pending",
                "payment_method": rental.payment.payment_method if hasattr(rental, "payment") else "cash",
            }
            form = RentalForm(instance=rental, initial=initial_data)

    return render(request, "rentals/edit_rental.html", {"form": form, "rental": rental})






@login_required
def report_dashboard(request):
    customers = Customer.objects.all()
    products = ProductAsset.objects.all()

    customer_id = request.GET.get('customer')
    product_id = request.GET.get('product')
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')

  # rentals = Rental.objects.filter(status='completed')
    rentals = Rental.objects.select_related('asset', 'customer').all()
    customer_business = []
    customer_type = request.GET.get('customer_type')

    if customer_type == 'BNI':
        rentals = rentals.filter(customer__is_bni_member=True)
        selected_customers = Customer.objects.filter(is_bni_member=True)

    elif customer_type == 'Permanent':
        rentals = rentals.filter(customer__is_permanent=True)
        selected_customers = Customer.objects.filter(is_permanent=True)
    else:
        selected_customers = []

    for customer in selected_customers:
        total = Rental.objects.filter(customer=customer).aggregate(total=Sum('price'))['total'] or 0
        customer_business.append({'name': customer.name, 'total': total})

    product_obj = None
    if product_id:
        try:
            product_obj = ProductAsset.objects.get(id=product_id)
        except ProductAsset.DoesNotExist:
            product_obj = None

    gross_profit = maintenance_cost = net_profit = None
    sold_asset = 0.0
    if product_obj:
        purchase_price = float(product_obj.purchase_price or 0)
        gross_profit = float(product_obj.total_rent_earned or 0)
        if product_obj.condition_status=='sold' and product_obj.sale_price:
            # gross_profit += float(product_obj.sale_price)
            sold_asset = float(product_obj.sale_price or 0)
        else:
            sold_asset = 0.0
        maintenance_cost = float(product_obj.total_repairs or 0)
        net_profit =  gross_profit - maintenance_cost -  purchase_price 



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
    total_days = float(sum((r.rental_end_date - r.rental_start_date).days for r in rentals if r.rental_end_date and r.rental_start_date))
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
        'purchase_price': product_obj.purchase_price if product_obj else 0,
        'gross_profit': gross_profit,
        'sold_asset': sold_asset,
        'maintenance_cost': maintenance_cost,
        'total_days': total_days,
        'net_profit': net_profit,
        'product_obj': product_obj, 
        'product_id': product_id,
        'gross_profit': gross_profit,
        'maintenance_cost': maintenance_cost,
        'net_profit': net_profit,
        'monthly_labels': json.dumps(list(reversed(monthly.keys()))),
        'monthly_values': json.dumps([float(v) for v in reversed(monthly.values())]),
        'top_assets': top_assets,
        'customer_business': customer_business,
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
            messages.success(request, "Vendor added successfully.")
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

    return render(request, 'rentals/add_repair.html', {'form': form, 'product': product})


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



@login_required
def edit_config(request, config_id):
    config = get_object_or_404(ProductConfiguration, id=config_id)

    if request.user.is_superuser:
        form = ProductConfigurationForm(request.POST or None, instance=config)
        if request.method == 'POST' and form.is_valid():
            form.save()
            return redirect('product_detail', pk=config.asset.pk)
    else:
        if request.method == 'POST':
            form = ProductConfigurationForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                pending = PendingProductConfiguration(
                    asset=config.asset,
                    ram=data['ram'],
                    hdd=data['hdd'],
                    ssd=data['ssd'],
                    graphics=data['graphics'],
                    display_size=data['display_size'],
                    power_supply=data['power_supply'],
                    detailed_config=data['detailed_config'],
                    submitted_by=request.user,
                    is_edit=True,
                    original_config=config,
                )
                pending.save()
                return redirect('product_detail', pk=config.asset.pk)
        else:
            form = ProductConfigurationForm(instance=config)

    return render(request, 'rentals/edit_config.html', {'form': form, 'config': config})


@login_required
def edit_repair(request, pk):
    repair = get_object_or_404(Repair, pk=pk)

    if request.user.is_superuser:
        form = RepairForm(request.POST or None, instance=repair)
        if request.method == 'POST' and form.is_valid():
            form.save()
            return redirect('product_detail', pk=repair.product.pk)
    else:
        if request.method == 'POST':
            form = RepairForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                pending = PendingRepair(
                    product=repair.product,
                    asset=repair.asset,
                    repair_date=data['repair_date'],
                    issue=data['issue'],
                    cost=data['cost'],
                    submitted_by=request.user,
                    is_edit=True,
                    original_repair=repair,
                )
                pending.save()
                return redirect('product_detail', pk=repair.product.pk)
        else:
            form = RepairForm(instance=repair)

    return render(request, 'rentals/edit_repair.html', {'form': form, 'repair': repair})




@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_edited_config(request, pk):
    pending = get_object_or_404(PendingProductConfiguration, pk=pk)
    config = pending.original_config

    # Apply changes
    config.ram = pending.ram
    config.hdd = pending.hdd
    config.ssd = pending.ssd
    config.graphics = pending.graphics
    config.display_size = pending.display_size
    config.power_supply = pending.power_supply
    config.detailed_config = pending.detailed_config
    config.save()

    pending.delete()
    messages.success(request, "Configuration update approved.")
    return redirect('approval_dashboard')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_edited_config(request, pk):
    pending = get_object_or_404(PendingProductConfiguration, pk=pk)
    pending.delete()
    messages.info(request, "Configuration update rejected.")
    return redirect('approval_dashboard')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_edited_repair(request, pk):
    pending = get_object_or_404(PendingRepair, pk=pk)
    repair = pending.original_repair

    repair.product = pending.product
    repair.issue_reported = pending.issue_reported
    repair.resolution = pending.resolution
    repair.cost = pending.cost
    repair.repair_date = pending.repair_date
    repair.save()

    pending.delete()
    messages.success(request, "Repair update approved.")
    return redirect('approval_dashboard')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_edited_repair(request, pk):
    pending = get_object_or_404(PendingRepair, pk=pk)
    pending.delete()
    messages.info(request, "Repair update rejected.")
    return redirect('approval_dashboard')



@login_required
def check_contracts(request):
    today = now().date()

    expired_rentals = Rental.objects.filter(
        contract_validity__isnull=False,
        contract_validity__lt=today,
        status="ongoing",
    )

    body_lines = []
    for rental in expired_rentals:
        asset_id = rental.asset.asset_id if rental.asset else 'Unknown'
        customer_name = rental.customer.name if rental.customer else 'Unknown Customer'
        body_lines.append(f"- Asset: {asset_id} | Customer: {customer_name}")

    body = "Contract Expiry Reminder:\n\n" + "\n".join(body_lines)
    # for rental in expired_rentals:
    #     subject = f"Contract Expired for Rental #{rental.id}"
    #     message = f"""
    #     """

        # message = f"""
        # Hello {rental.customer.name},

        # Your rental contract for asset {rental.asset.asset_id} has expired on {rental.contract_validity}.

        # Please return or renew your rental as soon as possible.
        # """
    if rental.customer.email:
            # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [rental.customer.email])
            send_mail(
            subject="Todays Contract Expiry Reminder",
            message=body,
            from_email='aryanpore3056@gmail.com',
            recipient_list=['aryanpore3056@gmail.com'],
            fail_silently=False,
            )
    
    messages.success(request, f"Checked {expired_rentals.count()} rentals for contract expiry.")
    return redirect("rental_list")
