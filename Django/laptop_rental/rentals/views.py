from django.shortcuts import render, redirect, get_object_or_404
from .models import Rental, Customer, ProductAsset, ProductConfiguration,Repair, PendingProduct, PendingCustomer, PendingRental, PendingProductConfiguration, Supplier, AssetType,CPUOption, HDDOption, RAMOption, DisplaySizeOption, GraphicsOption, PendingRepair, UserProfile
from .forms import CustomerForm, ProductAssetForm, ProductConfigurationForm, RentalForm, PendingCustomerForm, PendingRentalForm, PendingProductConfigurationForm, SupplierForm, RepairForm, AssetTypeForm,CPUOptionForm,  HDDOptionForm, RAMOptionForm, DisplaySizeOptionForm, GraphicsOptionForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from django.db import IntegrityError
from django.contrib import messages
from django.utils.timezone import now
from django.utils.dateparse import parse_date
from .utils import get_changed_fields
import uuid
from datetime import date,timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from datetime import datetime
import json
from collections import defaultdict
import csv
import pandas as pd
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from django.urls import reverse
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_HALF_UP
from .site_logger import log_action
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from .models import ProductAsset, ProductConfiguration
from .forms import ProductConfigurationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ProductAssetForm, PendingProductForm
from .models import ProductAsset, PendingProduct

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from .models import (
    Customer, PendingCustomer, ProductAsset, PendingProduct, ProductConfiguration,
    PendingProductConfiguration, Rental, PendingRental, Repair, PendingRepair,
    Supplier, AssetType, CPUOption, HDDOption, RAMOption, GraphicsOption, DisplaySizeOption
)
from io import StringIO, BytesIO
from zipfile import ZipFile
import pandas as pd
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from dal import autocomplete
from .models import Customer, ProductAsset, Rental
from django.db.models import Q

from dal import autocomplete
from django.core.cache import cache
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Rental, ProductAsset
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from collections import defaultdict
from django.db.models import Sum
from django.shortcuts import render
from django.utils.dateparse import parse_date
import json
from .models import Customer, ProductAsset, Rental, Repair, ProductConfiguration
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import RentalForm, PendingRentalForm
from .models import Rental
from django.db.models import Count, Q
from django.utils import timezone
from .forms import RentalBulkHeaderForm, RentalItemFormSet
from django.db.models import Subquery, OuterRef
from .models import AssetType, CPUOption, RAMOption, HDDOption
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Subquery, OuterRef, Prefetch
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User

@login_required
def short_term_calculator(request):
    # log_action(
    #         request.user,
    #         "revnue calculator",
    #         "Revenue calculator",
    #         changes=[f"Name: {asset_type.name}"],
    #         object_repr=asset_type.name
    #     )
    return render(request, 'rentals/short_term_calculator.html')


def logout_view(request):
    logout(request)
    log_action(request.user, "Logged out", "User")
    return redirect('login')


def set_global_year(request):
    year = request.GET.get('year')
    if year:
        request.session['selected_year'] = int(year)

    # Redirect to the previous page's path (without query parameters)
    # to prevent old ?year=... in the URL from overriding our new selection
    referer = request.META.get('HTTP_REFERER', '/')
    path = referer.split('?')[0]  # Strip old query params
    return redirect(path)


@login_required
def homepage(request):
    today = timezone.now().date()

    # 1. Existing KPIs
    active_rentals = Rental.objects.filter(status='ongoing').count()

    rented_asset_ids = Rental.objects.filter(status='ongoing').values_list('asset_id', flat=True)
    available_stock = ProductAsset.objects.filter(condition_status='working').exclude(id__in=rented_asset_ids).count()

    # 2. 🔴 NEW: Overdue Rentals (End date is in the past, but status is still ongoing)
    overdue_rentals = Rental.objects.filter(
        status='ongoing',
        rental_end_date__lt=today
    ).count()

    # 3. 🟡 NEW: Due Returns (Ending Today or Tomorrow)
    due_soon = Rental.objects.filter(
        status='ongoing',
        rental_end_date__range=[today, today + timedelta(days=1)]
    ).count()

    # 4. 💰 NEW: Revenue This Month (Simple estimation based on active rentals)
    # This sums up the monthly payment amount of all currently active rentals
    monthly_revenue = Rental.objects.filter(status='ongoing').aggregate(Sum('payment_amount'))['payment_amount__sum'] or 0

    # 5. Existing Alerts
    pending_approvals = 0
    if request.user.is_superuser:
        pending_approvals = (
            PendingProduct.objects.count() +
            PendingCustomer.objects.count() +
            PendingRental.objects.count() +
            PendingRepair.objects.count()
        )


    recent_logs = LogEntry.objects.select_related('content_type', 'user').order_by('-action_time')[:5]
    all_users = User.objects.exclude(id=request.user.id).select_related('profile').order_by('-last_login')

    processed_users = []
    now = timezone.now()

    for u in all_users:
        # Safely access profile (in case of old data issues)
        try:
            last_active = u.profile.last_activity
        except UserProfile.DoesNotExist:
            last_active = None

        # Attach the REAL last active time (fallback to last_login if empty)
        u.display_last_active = last_active if last_active else u.last_login

        # Determine Online Status (Active within last 5 mins)
        if last_active and (now - last_active).total_seconds() < 300:
            u.is_online = True
        else:
            u.is_online = False

        processed_users.append(u)

    # Sort: Online users first, then by most recent activity
    processed_users.sort(key=lambda x: (not x.is_online, -(x.display_last_active.timestamp() if x.display_last_active else 0)))

    recent_users = processed_users[:5]
    context = {
        'active_rentals': active_rentals,
        'available_stock': available_stock,
        'pending_approvals': pending_approvals,

        # New Context Variables
        'overdue_rentals': overdue_rentals,
        'due_soon': due_soon,
        'monthly_revenue': monthly_revenue,

        # new
        'recent_logs' :recent_logs,
        'recent_users': recent_users,
    }
    return render(request, 'homepage.html', context)



# views.py

@login_required
def smart_asset_search(request):
    # 1. Get Filter Parameters
    asset_type_id = request.GET.get('asset_type')
    cpu_id = request.GET.get('cpu')
    ram_id = request.GET.get('ram')
    hdd_id = request.GET.get('hdd')
    display_id = request.GET.get('display')
    graphics_id = request.GET.get('graphics')

    # --- NEW: Text Field Filters ---
    ssd_val = request.GET.get('ssd')
    power_val = request.GET.get('power')

    # --- NEW: Sorting & Availability ---
    show_available_only = request.GET.get('available_only') == 'true'
    sort_by = request.GET.get('ordering', 'asset_id') # Default sort

    # 2. Base Query
    assets = ProductAsset.objects.all()

    # 3. Apply Filters
    if asset_type_id:
        assets = assets.filter(type_of_asset_id=asset_type_id)

    # Subquery for latest config filtering
    # We filter if ANY config parameter is present
    if any([cpu_id, ram_id, hdd_id, display_id, graphics_id, ssd_val, power_val]):
        latest_config_subquery = ProductConfiguration.objects.filter(
            asset=OuterRef('pk')
        ).order_by('-date_of_config').values('id')[:1]

        assets = assets.filter(configurations__id=Subquery(latest_config_subquery))

        if cpu_id: assets = assets.filter(configurations__cpu_id=cpu_id)
        if ram_id: assets = assets.filter(configurations__ram_id=ram_id)
        if hdd_id: assets = assets.filter(configurations__hdd_id=hdd_id)
        if display_id: assets = assets.filter(configurations__display_size_id=display_id)
        if graphics_id: assets = assets.filter(configurations__graphics_id=graphics_id)

        # --- NEW: Filter by CharFields ---
        if ssd_val: assets = assets.filter(configurations__ssd=ssd_val)
        if power_val: assets = assets.filter(configurations__power_supply=power_val)

    # 4. Prefetch for efficiency (Ensure configs are ordered by newest)
    from django.db.models import Prefetch
    config_prefetch = Prefetch(
        'configurations',
        queryset=ProductConfiguration.objects.order_by('-date_of_config')
    )

    ongoing_rentals_prefetch = Prefetch(
        'rentals',
        queryset=Rental.objects.filter(status__in=['ongoing', 'overdue']).select_related('customer'),
        to_attr='active_rental_list'
    )

    # 5. Availability Logic
    if show_available_only:
        assets = assets.filter(condition_status='working')
        active_ids = Rental.objects.filter(status__in=['ongoing', 'overdue']).values_list('asset_id', flat=True)
        assets = assets.exclude(id__in=active_ids)
        pending_ids = PendingRental.objects.filter(asset__isnull=False).values_list('asset_id', flat=True)
        assets = assets.exclude(id__in=pending_ids)

    # 6. Apply Sorting
    # Map friendly names to actual fields if needed, or just use field names
    if sort_by == 'asset_id_desc':
        assets = assets.order_by('-asset_id')
    elif sort_by == 'purchased_newest':
        assets = assets.order_by('-purchase_date')
    elif sort_by == 'purchased_oldest':
        assets = assets.order_by('purchase_date')
    else:
        # Default asc
        assets = assets.order_by('asset_id')

    assets = assets.select_related('type_of_asset').prefetch_related(
        config_prefetch,
        ongoing_rentals_prefetch
    )

    # --- NEW: Fetch Unique CharField Values for Dropdowns ---
    # exclude null/empty values for cleaner dropdowns
    ssd_options = ProductConfiguration.objects.exclude(ssd__isnull=True).exclude(ssd__exact='').values_list('ssd', flat=True).distinct().order_by('ssd')
    power_options = ProductConfiguration.objects.exclude(power_supply__isnull=True).exclude(power_supply__exact='').values_list('power_supply', flat=True).distinct().order_by('power_supply')

    context = {
        'assets': assets,
        'asset_types': AssetType.objects.all(),
        'cpu_options': CPUOption.objects.all(),
        'ram_options': RAMOption.objects.all(),
        'hdd_options': HDDOption.objects.all(),
        'display_options': DisplaySizeOption.objects.all(),
        'graphics_options': GraphicsOption.objects.all(),

        # --- NEW: Pass CharField Options ---
        'ssd_options': ssd_options,
        'power_options': power_options,

        # Preserve selections
        'selected_type': int(asset_type_id) if asset_type_id else None,
        'selected_cpu': int(cpu_id) if cpu_id else None,
        'selected_ram': int(ram_id) if ram_id else None,
        'selected_hdd': int(hdd_id) if hdd_id else None,
        'selected_display': int(display_id) if display_id else None,
        'selected_graphics': int(graphics_id) if graphics_id else None,
        'selected_ssd': ssd_val,
        'selected_power': power_val,
        'selected_sort': sort_by,
        'show_available_only': show_available_only
    }

    if request.headers.get('HX-Request'):
        return render(request, 'rentals/partials/smart_search_results.html', context)

    return render(request, 'rentals/smart_search.html', context)


@login_required
def global_search(request):
    query = request.GET.get('q', '').strip()

    if not query:
        return redirect('home')

    # --- EXISTING SEARCH LOGIC (UNCHANGED) ---
    customers = Customer.objects.filter(
        Q(name__icontains=query) |
        Q(email__icontains=query) |
        Q(phone_number_primary__icontains=query) |
        Q(phone_number_secondary__icontains=query)
    )

    products = ProductAsset.objects.filter(
        Q(asset_id__icontains=query) |
        Q(serial_no__icontains=query) |
        Q(model_no__icontains=query) |
        Q(brand__icontains=query)
    )

    # Attach renter info (existing logic)
    active_rentals_map = {
        r.asset_id: r.customer.name
        for r in Rental.objects.filter(status='ongoing').select_related('customer')
    }
    for p in products:
        p.current_renter_name = active_rentals_map.get(p.id)

    rentals = Rental.objects.filter(
        Q(contract_number__icontains=query)
    ).select_related('customer', 'asset')

    # --- NEW ADDITIONS START HERE ---

    # 4. Search Suppliers (Name, GSTIN, Contact info)
    suppliers = Supplier.objects.filter(
        Q(name__icontains=query) |
        Q(gstin__icontains=query) |
        Q(email__icontains=query) |
        Q(phone_primary__icontains=query) |
        Q(reference_name__icontains=query)
    )

    # 5. Search Repairs (Issue description or Asset ID involved)
    repairs = Repair.objects.filter(
        Q(name__icontains=query) |  # The issue reported
        # Q(product__asset_id__icontains=query) |
        Q(info__icontains=query) # If you have a description field
    ).select_related('product')

    # 6. Search Configs (Find assets by CPU, RAM, etc. e.g., "i5" or "16GB")
    # We find the *Assets* that match these configs
    found_configs = ProductConfiguration.objects.filter(
        Q(cpu__name__icontains=query) |
        Q(ram__name__icontains=query) |
        Q(hdd__name__icontains=query) |
        Q(graphics__name__icontains=query) |
        Q(ssd__icontains=query) |
        Q(detailed_config__icontains=query)
    ).select_related('asset', 'cpu', 'ram', 'hdd', 'graphics', 'display_size')

    # --- END NEW ADDITIONS ---

    # Calculate Total
    total_results = (
        customers.count() +
        products.count() +
        rentals.count() +
        suppliers.count() +
        repairs.count() +
        found_configs.count()
    )

    # Auto-jump logic (Updated)
    if total_results == 1:
        if customers.exists(): return redirect('customer_detail', pk=customers.first().pk)
        if products.exists(): return redirect('product_detail', pk=products.first().pk)
        if suppliers.exists(): return redirect('edit_supplier', pk=suppliers.first().pk)
        # We generally don't auto-redirect to repairs as they are sub-items

    return render(request, 'global_search.html', {
        'query': query,
        'customers': customers,
        'products': products,
        'found_configs': found_configs, # Pass this separately or combine in template
        'rentals': rentals,
        'suppliers': suppliers,
        'repairs': repairs,
        'total_results': total_results
    })


from datetime import timedelta
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail

@login_required
def expiry_dashboard(request):
    today = timezone.now().date()
    warning_date = today + timedelta(days=15)  # Look ahead 15 days

    # 1. FETCH DATA
    # Already Expired
    expired_rentals = Rental.objects.filter(
        contract_validity__isnull=False,
        contract_validity__lt=today,
        status="ongoing",
    ).select_related('customer', 'asset').order_by('contract_validity')

    # Expiring Soon (Next 15 Days)
    expiring_soon = Rental.objects.filter(
        contract_validity__isnull=False,
        contract_validity__gte=today,
        contract_validity__lte=warning_date,
        status="ongoing",
    ).select_related('customer', 'asset').order_by('contract_validity')

    # 2. HANDLE EMAIL SENDING (Only when button is clicked)
    if request.method == "POST" and 'send_reminders' in request.POST:
        if not expired_rentals.exists():
            messages.info(request, "No expired contracts to remind.")
        else:
            # Build Email Content
            body_lines = ["The following rental contracts have expired:\n"]
            recipient_list = ['accounts@pixelitsolution.com', 'support@pixelitsolution.com', 'rental@pixelitsolution.com'] # Admin email

            for rental in expired_rentals:
                line = f"- {rental.customer.name} | Asset: {rental.asset.asset_id} | Expired: {rental.contract_validity}"
                body_lines.append(line)

                # OPTIONAL: Add customer email to list if you want to CC them?
                # if rental.customer.email:
                #     recipient_list.append(rental.customer.email)

            body_lines.append("\nPlease take necessary action.")

            try:
                send_mail(
                    subject="Rental Management System - Contract Notification",
                    message="\n".join(body_lines),
                    from_email='support@pixelitsolution.com',
                    recipient_list=recipient_list,
                    fail_silently=False,
                )
                messages.success(request, f"✅ Reminder sent for {expired_rentals.count()} expired contracts.")
            except Exception as e:
                messages.error(request, f"❌ Failed to send email: {e}")

        # Redirect to avoid resending on refresh
        return redirect('check_contracts')

    # 3. RENDER DASHBOARD
    return render(request, 'rentals/check_contracts.html', {
        'expired_rentals': expired_rentals,
        'expiring_soon': expiring_soon,
        'today': today
    })

@login_required
def sold_assets(request):
    products = ProductAsset.objects.filter(condition_status='sold').order_by('-sale_date')
    return render(request, 'rentals/sold_assets.html', {'products': products})

@login_required
def shortcuts(request):
    return render(request,'rentals/shortcuts.html')
@login_required
def settings_page(request):
    # 1. Get ALL logs (remove the [:10] slice)
    log_list = LogEntry.objects.select_related('content_type', 'user').order_by('-action_time')

    # 2. Set up Paginator (10 items per page)
    paginator = Paginator(log_list, 10)

    # 3. Get current page number from URL (e.g. ?page=2)
    page_number = request.GET.get('page')

    try:
        recent_logs = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        recent_logs = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results.
        recent_logs = paginator.page(paginator.num_pages)

    context = {'recent_logs': recent_logs}
    return render(request, 'settings.html', context)


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
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', 'asset_id')
    asset_type = request.GET.get('type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    current_year = datetime.now().year

    # 1. Get from session
    raw_year = request.session.get('selected_year', current_year)

    # 2. FORCE INTEGER CONVERSION HERE
    try:
        selected_year = int(raw_year)
    except:
        selected_year = current_year

    products = ProductAsset.objects.all()
    # Filter using string version for DB, but keep 'selected_year' as INT for Template
    products = products.filter(asset_id__icontains=str(selected_year))    # ---- OTHER FILTERS ----
    if start_date:
        products = products.filter(purchase_date__gte=parse_date(start_date))

    if end_date:
        products = products.filter(purchase_date__lte=parse_date(end_date))

    active_rentals = {
        rental.asset.id: rental.customer.name
        for rental in Rental.objects.filter(status='ongoing')
        if rental.asset
    }

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

    # You *can* drop this if you move year_list to context processor, but keeping for now:
    year_list = list(range(2015, datetime.now().year + 1))

    return render(request, 'rentals/product_list.html', {
        'products': products,
        'query': query,
        'sort_by': sort_by,
        'asset_type': asset_type,
        'asset_types': asset_types,
        'year_list': year_list,
        'selected_year': int(selected_year),   # important for UI
        'start_date': start_date,
        'end_date': end_date,
        'active_rentals': active_rentals,
    })




@login_required
@user_passes_test(lambda u: u.is_superuser)
def asset_type_list(request):
    asset_types = AssetType.objects.all()
    return render(request, 'products/asset_type_list.html', {'asset_types': asset_types})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_asset_type(request):
    form = AssetTypeForm(request.POST or None)
    if form.is_valid():
        asset_type = form.save()

        # Smart Log
        log_action(
            request.user,
            "Created Asset Type",
            "AssetType",
            obj_id=asset_type.id,
            changes=[f"Name: {asset_type.name}"],
            object_repr=asset_type.name
        )
        return redirect('asset_type_list')
    return render(request, 'products/add_asset_type.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_asset_type(request, pk):
    old_instance = AssetType.objects.get(pk=pk) # Capture state
    asset_type = get_object_or_404(AssetType, pk=pk)
    form = AssetTypeForm(request.POST or None, instance=asset_type)
    if form.is_valid():
        updated_type = form.save()

        # Diff
        changes = get_changed_fields(old_instance, updated_type)

        log_action(
            request.user,
            "Edited Asset Type",
            "AssetType",
            obj_id=updated_type.id,
            changes=changes,
            object_repr=updated_type.name
        )
        return redirect('asset_type_list')
    return render(request, 'products/edit_asset_type.html', {'form': form})



@login_required
def approval_dashboard(request):
    pending_products = PendingProduct.objects.all()
    pending_customers = PendingCustomer.objects.all()
    pending_rentals = PendingRental.objects.all()
    pending_configs = PendingProductConfiguration.objects.all()
    pending_repairs = PendingRepair.objects.select_related('product', 'original_repair', 'submitted_by')


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
    repairs_data = [
        {"pending": pr, "old": pr.original_repair} for pr in pending_repairs
    ]

    return render(request, "rentals/approval_dashboard.html", {
        "pending_products": products_data,
        "pending_customers": customers_data,
        "pending_rentals": rentals_data,
        "pending_configs": configs_data,
        "pending_repairs": repairs_data,
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
        edited_by=pending.submitted_by,
        edited_at= pending.submitted_at
    )
    details = [
        f"Asset: {config.asset.asset_id}",
        f"CPU: {config.cpu}",
        f"RAM: {config.ram}",
        f"SSD: {config.ssd}"
    ]

    log_action(
        request.user,
        "Approved Configuration",
        "ProductConfiguration",
        obj_id=config.id,
        changes=details,
        object_repr=f"Config {config.id}"
    )
    pending.delete()
    return redirect('approval_dashboard')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_config(request, pk):
    pending = get_object_or_404(PendingProductConfiguration, pk=pk)
    details = [f"Asset: {pending.asset.asset_id}", f"RAM: {pending.ram}", f"SSD: {pending.ssd}"]

    log_action(
        request.user,
        "Rejected configuration",
        "PendingProductConfiguration",
        obj_id=pending.id,
        changes=details,
        object_repr=f"Req Config {pending.asset.asset_id}"
    )
    pending.delete()
    return redirect('approval_dashboard')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_product(request, pk):
    pending = get_object_or_404(PendingProduct, pk=pk)

    try:
        if pending.pending_type == "edit" and pending.original_product:
            product = pending.original_product

            changes = get_changed_fields(product, pending)
            # tell product.save() to ignore this pending record when checking PendingProduct table
            product._pending_pk = pending.pk
            # product.asset_id = pending.asset_id   # REQUIRED FIX

            # copy fields (do NOT overwrite asset_id here)
            for field in [
                "asset_id","asset_suffix",
                "type_of_asset", "brand", "model_no", "serial_no",
                "purchase_price", "current_value", "purchase_date",
                "under_warranty", "warranty_duration_months",
                "purchased_from", "condition_status", "asset_number",
                "sold_to", "sale_price", "sale_date",
                "date_marked_dead", "damage_narration",
            ]:
                setattr(product, field, getattr(pending, field))

            product.edited_by = pending.submitted_by
            # product.edited_at = pending.submitted_at
            PendingProduct.objects.filter(
                asset_id=pending.asset_id
            ).exclude(pk=pending.pk).delete()

            product.save()
            pending.delete()
            log_action(
                request.user,
                "Approved Product Edit",
                "ProductAsset",
                obj_id=product.id,
                changes=changes,
                object_repr=product.asset_id
            )
        else:
            # New product (add/clone) — instantiate so we can set _pending_pk
            new_product = ProductAsset(
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
                asset_id=pending.asset_id,   # allowed for new products
                sold_to=pending.sold_to,
                sale_price=pending.sale_price,
                sale_date=pending.sale_date,
                date_marked_dead=pending.date_marked_dead,
                damage_narration=pending.damage_narration,
                edited_by=pending.submitted_by
            )

            # tell new_product.save() to ignore this pending record when checking PendingProduct table
            # new_product._pending_pk = pending.pk
            new_product.save()
            pending.delete()

            # Log Creation Details
            details = [f"Asset ID: {new_product.asset_id}", f"Model: {new_product.model_no}"]
            log_action(
                request.user,
                "Approved New Product",
                "ProductAsset",
                obj_id=new_product.id,
                changes=details,
                object_repr=new_product.asset_id
            )
        # only delete pending after successful save
        # pending.delete()
        messages.success(request, "✅ Product approved successfully.")
    except ValueError as e:
        # give a meaningful message and do not delete pending
        messages.error(request, f"Approval failed: {e}")
    except Exception as e:
        messages.error(request, f"Unexpected error during approval: {e}")

    return redirect("approval_dashboard")

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_product(request, pk):
    pending = get_object_or_404(PendingProduct, pk=pk)
    details = [f"Asset ID: {pending.asset_id}", f"Model: {pending.model_no}"]

    log_action(
        request.user,
        "Rejected product",
        "PendingProduct",
        obj_id=pending.id,
        changes=details,
        object_repr=pending.asset_id
    )
    pending.delete()
    return redirect('approval_dashboard')


@login_required
def rental_history(request):
    query = request.GET.get('q', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Start with all completed rentals
    rentals = Rental.objects.filter(status='completed')

    # 1. Text Search
    if query:
        rentals = rentals.filter(
            Q(customer__name__icontains=query) |
            Q(asset__asset_id__icontains=query) |
            Q(asset__model_no__icontains=query) |
            Q(contract_number__icontains=query)
        )

    # 2. Date Range Filter (Filter by when the rental ENDED)
    if start_date:
        rentals = rentals.filter(rental_end_date__gte=start_date)
    if end_date:
        rentals = rentals.filter(rental_end_date__lte=end_date)

    # Sort by newest end date first
    rentals = rentals.order_by('-rental_end_date')

    return render(request, 'rentals/rental_history.html', {
        'rentals': rentals,
        'query': query,
        'start_date': start_date,
        'end_date': end_date
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
                details = [f"Name: {customer.name}", f"Phone: {customer.phone_number_primary}"]
                log_action(
                    request.user,
                    "Added new customer",
                    "Customer",
                    obj_id=customer.id,
                    changes=details,
                    object_repr=customer.name
                )

                return redirect('customer_list')
        else:
            form = PendingCustomerForm(request.POST)
            if form.is_valid():
                pending = form.save(commit=False)
                pending.submitted_by = request.user
                pending.save()
                details = [f"Name: {pending.name}", f"Phone: {pending.phone_number_primary}"]
                log_action(
                    request.user,
                    "Added new customer (approval)",
                    "Customer",
                    obj_id=pending.id,
                    changes=details,
                    object_repr=pending.name
                )
                return redirect('customer_list')
    else:
        form = CustomerForm() if request.user.is_superuser else PendingCustomerForm()


    return render(request, 'rentals/add_customer.html', {'form': form})



@login_required
def add_product(request):
    form = ProductAssetForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        query_string = request.GET.urlencode()
        redirect_url = reverse('product_list')
        if query_string:
            redirect_url += f'?{query_string}'

        if request.user.is_superuser:
            # Directly save product for superuser
            product = form.save(commit=False)
            product.edited_by = request.user
            product.save()

            details = [
                f"Asset ID: {product.asset_id}",
                f"Model: {product.model_no}",
                f"Config: {product.type_of_asset}"
            ]
            log_action(
                request.user,
                "Created new product",
                "ProductAsset",
                obj_id=product.id,
                changes=details,
                object_repr=product.asset_id
            )

            messages.success(request, f"✅ Product '{product.asset_id}' was successfully created.")
            return redirect(redirect_url)

        else:
            # Non-superuser → create a PendingProduct
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
                asset_number=form.cleaned_data.get('asset_number'),
                asset_id=form.cleaned_data.get('asset_id'),
                sold_to=form.cleaned_data.get('sold_to'),
                sale_price=form.cleaned_data.get('sale_price'),
                sale_date=form.cleaned_data.get('sale_date'),
                date_marked_dead=form.cleaned_data.get('date_marked_dead'),
                damage_narration=form.cleaned_data.get('damage_narration'),
                submitted_by=request.user
            )
            pending.save()
            details = [
                f"Asset ID: {pending.asset_id}",
                f"Model: {pending.model_no}",
                f"Config: {pending.type_of_asset}"
            ]
            log_action(
                request.user,
                "Created new product",
                "ProductAsset",
                obj_id=pending.id,
                changes=details,
                object_repr=pending.asset_id
            )
            messages.success(request, f"Product {form.cleaned_data.get('asset_id')} submitted for approval and pending review.")
            return redirect(redirect_url)

    return render(request, 'rentals/add_product.html', {'form': form})




@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_customer(request, pk):
    pending = get_object_or_404(PendingCustomer, pk=pk)

    if pending.original_customer:
        customer = pending.original_customer
        changes = get_changed_fields(customer, pending)

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
        log_action(
            request.user,
            "Approved New Customer",
            "Customer",
            obj_id=customer.id,
            changes=[f"Name: {customer.name}"],
            object_repr=customer.name
        )
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
        log_action(
            request.user,
            "Approved New Customer",
            "Customer",
            obj_id=customer.id,
            changes=[f"Name: {customer.name}"],
            object_repr=customer.name
        )
    pending.delete()
    messages.success(request, "Customer approved successfully.")
    return redirect("approval_dashboard")

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_customer(request, pk):
    pending = get_object_or_404(PendingCustomer, pk=pk)

    details = [f"Name: {pending.name}", f"Phone: {pending.phone_number_primary}"]

    log_action(
        request.user,
        "Rejected customer",
        "PendingCustomer",
        obj_id=pending.id,
        changes=details,
        object_repr=pending.name
    )
    pending.delete()
    return redirect('approval_dashboard')


@login_required
def add_rental(request):
    if request.method == 'POST':
        if request.user.is_superuser:
            # ✅ Superuser directly creates rental
            form = RentalForm(request.POST)
            if form.is_valid():
                rental = form.save(commit=False)
                rental.edited_by = request.user
                rental.save()
                details = [
                    f"Customer: {rental.customer.name}",
                    f"Asset: {rental.asset.asset_id if rental.asset else 'None'}",
                    f"Start: {rental.rental_start_date}",
                    f"Amount: {rental.payment_amount}"
                ]
                log_action(
                    request.user,
                    "Created rental",
                    "Rental",
                    obj_id=rental.id,
                    changes=details,
                    object_repr=f"Rental #{rental.id}"
                )
                messages.success(request, "Rental added successfully.")
                return redirect('rental_list')

        else:
            # ✅ Normal user submits for approval
            form = PendingRentalForm(request.POST)
            if form.is_valid():
                pending = form.save(commit=False)
                pending.submitted_by = request.user
                pending.edited_by = request.user
                pending.save()
                details = [
                    f"Customer: {pending.customer}",
                    f"Asset: {pending.asset}",
                    f"Start: {pending.rental_start_date}"
                ]
                log_action(
                    request.user,
                    "Submitted rental for approval",
                    "PendingRental",
                    obj_id=pending.id,
                    changes=details,
                    object_repr=f"Req Rental {pending.asset}"
                )
                messages.success(request, "Rental submitted for approval.")

                return redirect('rental_list')
    else:
        form = RentalForm() if request.user.is_superuser else PendingRentalForm()

    return render(request, 'rentals/add_rental.html', {'form': form})



# In views.py
# In rentals/views.py

class AssetAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # 1. Check for Backdated Flag from the URL (sent by Javascript)
        is_backdated = self.request.GET.get('backdated') == 'true'

        if is_backdated:
            # === BACKDATED MODE ===
            # Show EVERY asset in the system (Rented, Sold, Working, etc.)
            # This allows you to log historical rentals for assets that are currently unavailable.
            qs = ProductAsset.objects.all().order_by('asset_id')

        else:
            # === NORMAL MODE ===
            # Strict filtering to prevent double-booking

            # A. Exclude currently rented (Ongoing/Overdue)
            rented_ids = Rental.objects.filter(
                status__in=['ongoing', 'overdue'],
                asset__isnull=False
            ).values_list('asset_id', flat=True)

            # B. Exclude assets currently in 'Pending Rental' approval queue
            # (This fixes your issue of seeing assets that are waiting for approval)
            pending_ids = PendingRental.objects.filter(
                asset__isnull=False
            ).values_list('asset_id', flat=True)

            # Combine exclusions
            excluded_ids = set(rented_ids) | set(pending_ids)

            # C. Apply Filter: Must be 'working' and NOT in the excluded list
            qs = ProductAsset.objects.filter(
                condition_status='working'
            ).exclude(id__in=excluded_ids).order_by('asset_id')

        # 2. Apply Text Search (Common to both modes)
        if self.q:
            qs = qs.filter(
                Q(asset_id__icontains=self.q) |
                Q(brand__icontains=self.q) |
                Q(model_no__icontains=self.q) |
                Q(serial_no__icontains=self.q)
            )
        return qs

    def get_result_label(self, item):
        # Optional: Add status to label for clarity in backdated mode
        if self.request.GET.get('backdated') == 'true':
            return f"{item.asset_id} - {item.brand} ({item.condition_status})"
        return f"{item.asset_id} - {item.brand} {item.model_no}"


@login_required
def add_bulk_rental(request):
    # Check if backdated mode is active from URL
    is_backdated = request.GET.get('backdated') == 'true'

    if request.method == 'POST':
        header_form = RentalBulkHeaderForm(request.POST)

        # Pass the backdated flag to the FormSet
        formset = RentalItemFormSet(request.POST, form_kwargs={'backdated': is_backdated})

        if header_form.is_valid() and formset.is_valid():
            header_data = header_form.cleaned_data
            rentals_created = 0

            for form in formset:
                if form.cleaned_data:
                    asset = form.cleaned_data.get('asset')
                    raw_amount = form.cleaned_data.get('payment_amount')
                    amount = raw_amount if raw_amount is not None else 0

                    if asset:
                        # Determine Status: Force 'completed' if backdated, else use form selection
                        final_status = 'completed' if is_backdated else header_data['status']

                        if request.user.is_staff or request.user.is_superuser:
                            rental_obj =Rental.objects.create(
                                customer=header_data['customer'],
                                rental_start_date=header_data['rental_start_date'],
                                rental_end_date=header_data['rental_end_date'],
                                billing_day=header_data['billing_day'],
                                contract_number=header_data['contract_number'],
                                contract_validity=header_data['contract_validity'],
                                status=final_status,
                                asset=asset,
                                payment_amount=amount,
                                edited_by=request.user
                            )
                            details = [
                                f"Customer: {header_data['customer']}",
                                f"Asset: {asset.asset_id}",
                                f"Amount: {amount}",
                                f"Start: {header_data['rental_start_date']}"
                            ]

                            log_action(
                                request.user,
                                "Created Bulk Rental",
                                "Rental" if request.user.is_staff else "PendingRental",
                                obj_id=rental_obj.id,
                                changes=details,
                                object_repr=f"Rental {asset.asset_id}"
                            )
                            rentals_created += 1
                        else:
                            pending_obj = PendingRental.objects.create(
                                customer=header_data['customer'],
                                rental_start_date=header_data['rental_start_date'],
                                rental_end_date=header_data['rental_end_date'],
                                billing_day=header_data['billing_day'],
                                contract_number=header_data['contract_number'],
                                contract_validity=header_data['contract_validity'],
                                status=final_status,
                                asset=asset,
                                payment_amount=amount,
                                submitted_by=request.user,
                            )
                            details = [
                                f"Customer: {header_data['customer']}",
                                f"Asset: {asset.asset_id}",
                                f"Amount: {amount}"
                            ]
                            log_action(
                                request.user,
                                "Submitted Bulk Rental",
                                "PendingRental",
                                obj_id=pending_obj.id,
                                changes=details,
                                object_repr=f"Req Rental {asset.asset_id}"
                            )
                        rentals_created += 1

            if rentals_created > 0:
                msg = f"Successfully added {rentals_created} backdated entries." if is_backdated else f"Successfully added {rentals_created} rentals."
                messages.success(request, msg)
            else:
                messages.warning(request, "No valid assets were selected.")

            return redirect('rental_list')
    else:
        header_form = RentalBulkHeaderForm()
        # Pass backdated flag to empty formset too
        formset = RentalItemFormSet(form_kwargs={'backdated': is_backdated})

    return render(request, 'rentals/add_bulk_rental.html', {
        'header_form': header_form,
        'formset': formset
    })



@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_rental(request, pk):
    pending = get_object_or_404(PendingRental, pk=pk)

    if pending.original_rental:
        # ✅ Update existing rental
        rental = pending.original_rental

        changes = get_changed_fields(rental, pending)

        rental.customer = pending.customer
        rental.asset = pending.asset
        rental.rental_start_date = pending.rental_start_date
        rental.rental_end_date = pending.rental_end_date
        rental.billing_day = pending.billing_day
        rental.contract_number = pending.contract_number
        rental.contract_validity = pending.contract_validity
        rental.status = pending.status
        rental.payment_amount = pending.payment_amount
        rental.edited_by = pending.submitted_by
        rental.edited_at = pending.submitted_at
        rental.save()

        log_action(
            request.user,
            "Approved Rental Edit",
            "Rental",
            obj_id=rental.id,
            changes=changes,
            object_repr=f"Rental {rental.id}"
        )
    else:
        # ✅ Create new rental
        rental = Rental.objects.create(
            customer=pending.customer,
            asset=pending.asset,
            rental_start_date=pending.rental_start_date,
            rental_end_date=pending.rental_end_date,
            billing_day=pending.billing_day,
            contract_number=pending.contract_number,
            contract_validity=pending.contract_validity,
            status=pending.status,
            payment_amount=pending.payment_amount,
            edited_by=pending.submitted_by,
        )
        details = [f"Customer: {rental.customer}", f"Asset: {rental.asset}"]
        log_action(
            request.user,
            "Approved New Rental",
            "Rental",
            obj_id=rental.id,
            changes=details,
            object_repr=f"Rental {rental.id}"
        )
    # ✅ Remove pending request after approval
    pending.delete()
    messages.success(request, "Rental approved successfully.")
    return redirect("approval_dashboard")

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_rental(request, pk):
    pending = get_object_or_404(PendingRental, pk=pk)

    details = [f"Customer: {pending.customer}", f"Asset: {pending.asset}"]

    log_action(
        request.user,
        "Rejected rental",
        "PendingRental",
        obj_id=pending.id,
        changes=details,
        object_repr=f"Req Rental {pending.asset}"
    )
    pending.delete()
    return redirect('approval_dashboard')



@login_required
def edit_rental(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id)
    old_instance = Rental.objects.get(pk=rental_id)
    if request.user.is_superuser:
        # ✅ Superuser can edit directly
        form = RentalForm(request.POST or None, instance=rental)
        if request.method == "POST" and form.is_valid():
            updated_rental = form.save(commit=False)

            # 2. Calculate Differences
            changes = get_changed_fields(old_instance, updated_rental)

            updated_rental.edited_by = request.user
            updated_rental.save()

            # 3. Log Smart Changes
            log_action(
                request.user,
                "Edited rental",
                "Rental",
                obj_id=updated_rental.id,
                changes=changes,
                object_repr=f"Rental #{updated_rental.id}"
            )
            messages.success(request, "Rental updated successfully.")
            return redirect("rental_list")

    else:
        # ✅ Normal user submits edit for approval
        if request.method == "POST":
            form = RentalForm(request.POST, instance=rental)
            if form.is_valid():
                cleaned = form.cleaned_data
                pending = PendingRental(
                    original_rental=rental,
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
                changes = get_changed_fields(rental, pending)

                # 2. Log
                log_action(
                    request.user,
                    "Requested Rental Edit",
                    "PendingRental",
                    obj_id=pending.id,
                    changes=changes,
                    object_repr=f"Req for Rental {rental.id}"
                )
                messages.success(request, "Rental changes submitted for approval.")
                return redirect("rental_list")
        else:
            form = RentalForm(instance=rental)

    return render(request, "rentals/edit_rental.html", {"form": form, "rental": rental})


@login_required
def edit_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    old_instance = Customer.objects.get(pk=pk)

    if request.user.is_superuser:
        form = CustomerForm(request.POST or None, instance=customer)
        if request.method == "POST" and form.is_valid():
            updated_customer = form.save(commit=False)

            # 4. Calculate Differences
            changes = get_changed_fields(old_instance, updated_customer)

            updated_customer.edited_by = request.user
            updated_customer.save()

            # 5. Log with specific details
            log_action(
                request.user,
                "Edited customer",
                "Customer",
                obj_id=updated_customer.id,
                changes=changes,             # <--- Passing the differences
                object_repr=updated_customer.name
            )

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

                # Capture Changes
                changes = get_changed_fields(customer, pending)

                log_action(
                    request.user,
                    "Requested Customer Edit",
                    "PendingCustomer",
                    obj_id=pending.id,
                    changes=changes,
                    object_repr=f"Req for {customer.name}"
                )
                messages.success(request, "Customer changes submitted for approval.")
                return redirect("customer_list")
        else:
            form = CustomerForm(instance=customer)

    return render(request, "rentals/edit_customer.html", {"form": form, "customer": customer})


@login_required
def edit_product(request, pk):
    product = get_object_or_404(ProductAsset, pk=pk)
    form = ProductAssetForm(request.POST or None, instance=product)
    old_instance = ProductAsset.objects.get(pk=pk)
    # Preserve filters
    query_string = request.GET.urlencode()
    redirect_url = reverse('product_list')
    if query_string:
        redirect_url += f'?{query_string}'

    if request.method == 'POST' and form.is_valid():
        if request.user.is_superuser:
            # Direct edit by superuser
            updated_product = form.save(commit=False)

            # 2. Calculate Differences
            changes = get_changed_fields(old_instance, updated_product)

            updated_product.edited_by = request.user
            updated_product.save()

            # 3. Log Smart Changes
            log_action(
                request.user,
                "Edited product",
                "ProductAsset",
                obj_id=updated_product.id,
                changes=changes,
                object_repr=updated_product.asset_id
            )
            messages.success(request, f"✏️ Product '{product.asset_id}' was successfully updated.")
            return redirect(redirect_url)

        else:
            # Save as pending edit for approval
            cleaned = form.cleaned_data
            pending_obj = PendingProduct.objects.create(
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
                sold_to=cleaned.get('sold_to'),
                sale_price=cleaned.get('sale_price'),
                sale_date=cleaned.get('sale_date'),
                date_marked_dead=cleaned.get('date_marked_dead'),
                damage_narration=cleaned.get('damage_narration'),
            )
            changes = get_changed_fields(product, pending_obj)

            # 2. Log with "Requested Changes"
            log_action(
                request.user,
                "Requested Product Edit",
                "PendingProduct",
                obj_id=pending_obj.id,
                changes=changes,
                object_repr=f"Req for {product.asset_id}"
            )
            messages.success(request, "Changes submitted for approval.")
            return redirect(redirect_url)

    return render(request, 'rentals/edit_product.html', {
        'form': form,
        'product': product,
        'redirect_url': redirect_url
    })




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
                details = [
                    f"CPU: {config.cpu}",
                    f"RAM: {config.ram}",
                    f"SSD: {config.ssd}"
                ]
                log_action(
                    request.user,
                    "Added configuration",
                    "ProductConfiguration",
                    obj_id=config.id,
                    changes=details,
                    object_repr=f"Config for {asset.asset_id}"
                )
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

                # FIXED LOGGING
                details = [
                    f"Asset: {asset.asset_id}",
                    f"RAM: {pending.ram}",
                    f"SSD: {pending.ssd}"
                ]
                log_action(
                    request.user,
                    "Submitted config for approval",
                    "PendingProductConfiguration",
                    obj_id=pending.id,
                    changes=details,
                    object_repr=f"Req Config {asset.asset_id}"
                )
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
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    product = get_object_or_404(ProductAsset, pk=pk)

    # Fetch rentals specifically for this customer
    current_rentals = Rental.objects.filter(customer=customer, status='ongoing').select_related('asset')
    rental_history = Rental.objects.filter(customer=customer, status='completed').select_related('asset').order_by('-rental_end_date')
    active_count = current_rentals.count()
    history_count = rental_history.count()

    # Optional: Calculate total active monthly billing for this customer
    total_active_billing = current_rentals.aggregate(Sum('payment_amount'))['payment_amount__sum'] or 0

    return render(request, 'rentals/customer_detail.html', {
        'product': product,
        'customer': customer,
        'current_rentals': current_rentals,
        'rental_history': rental_history,
        'total_active_billing': total_active_billing,
        'active_count': active_count,
        'history_count': history_count,

    })


@login_required
def product_detail(request, pk):
    product = get_object_or_404(ProductAsset, pk=pk)
    configs = product.configurations.all().order_by('-date_of_config')
    repairs = product.repairs.all().order_by('-date')
    current_rentals = Rental.objects.filter(asset=product, status='ongoing').select_related('customer')
    rental_history = Rental.objects.filter(asset=product, status='completed').select_related('customer')

    total_history_revenue = Decimal('0.00')
    today = timezone.now().date()


    for rental in rental_history:
        rental.calculated_revenue = Decimal('0.00')

        # Only calculate if we have a valid start date and payment amount
        if rental.rental_start_date and rental.payment_amount and rental.payment_amount > 0:
            end_date = rental.rental_end_date or today
            if end_date > today:
                end_date = today

            if rental.rental_start_date <= end_date:
                total_rental_revenue = Decimal('0.00')
                current_date = rental.rental_start_date

                while current_date <= end_date:
                    if current_date.month == 12:
                        next_month_start = date(current_date.year + 1, 1, 1)
                    else:
                        next_month_start = date(current_date.year, current_date.month + 1, 1)

                    days_in_month = (next_month_start - timedelta(days=1)).day

                    if current_date.month == end_date.month and current_date.year == end_date.year:
                        end_day = end_date.day
                    else:
                        end_day = days_in_month

                    days_to_count = end_day - current_date.day + 1
                    daily_rate = rental.payment_amount / Decimal(days_in_month)
                    total_rental_revenue += (daily_rate * Decimal(days_to_count))

                    current_date = next_month_start

                # Round and assign to this specific rental object
                rental.calculated_revenue = total_rental_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Add to the running total
        total_history_revenue += rental.calculated_revenue

    query_string = request.GET.urlencode()
    redirect_url = reverse('product_list')
    if query_string:
        redirect_url += f'?{query_string}'

    return render(request, 'rentals/product_detail.html', {
        'product': product,
        'configs': configs,
        'repairs': repairs,
        'current_rentals': current_rentals,
        'rental_history': rental_history,
        'total_history_revenue': total_history_revenue,
        'redirect_url': redirect_url,
        })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_config(request, config_id):
    config = get_object_or_404(ProductConfiguration, pk=config_id)
    asset_id = config.asset.pk
    details = [f"RAM: {config.ram}", f"SSD: {config.ssd}", f"Asset: {config.asset.asset_id}"]

    log_action(
        request.user,
        "Deleted configuration",
        "ProductConfiguration",
        obj_id=config.id,
        changes=details,
        object_repr=f"Config {config.id}"
    )
    config.delete()
    return redirect('product_detail', pk=asset_id)

@login_required
def clone_product(request, pk):
    original = get_object_or_404(ProductAsset, pk=pk)

    # Preserve filters
    query_string = request.GET.urlencode()
    redirect_url = reverse('product_list')
    if query_string:
        redirect_url += f'?{query_string}'

    if request.user.is_superuser:
        # Clone directly for superuser
        new_product = ProductAsset(
            type_of_asset=original.type_of_asset,
            brand=original.brand,
            model_no=original.model_no,
            serial_no=original.serial_no,
            purchase_price=original.purchase_price,
            current_value=original.current_value,
            purchase_date=original.purchase_date,
            under_warranty=original.under_warranty,
            warranty_duration_months=original.warranty_duration_months,
            purchased_from=original.purchased_from,
            condition_status=original.condition_status,
            edited_by=request.user
        )
        new_product.save()
        details = [f"Source Asset: {original.asset_id}", f"New Model: {new_product.model_no}"]
        log_action(
            request.user,
            "Cloned product",
            "ProductAsset",
            obj_id=new_product.id,
            changes=details,
            object_repr=new_product.asset_id
        )
        messages.success(request, f"Product cloned successfully {new_product.asset_id}. Please update details as per need.")
        return redirect(redirect_url)

    else:
        new_product = PendingProduct(
            type_of_asset=original.type_of_asset,
            brand=original.brand,
            model_no=original.model_no,
            serial_no=original.serial_no,
            purchase_price=original.purchase_price,
            current_value=original.current_value,
            purchase_date=original.purchase_date,
            under_warranty=original.under_warranty,
            warranty_duration_months=original.warranty_duration_months,
            purchased_from=original.purchased_from,
            condition_status=original.condition_status,
            edited_by=request.user
        )
        new_product.save()
        details = [f"Source Asset: {original.asset_id}", "Waiting Approval"]
        log_action(
            request.user,
            "Requested Product Clone",
            "PendingProduct",
            obj_id=new_product.id,
            changes=details,
            object_repr=f"Clone Req {original.asset_id}"
        )
        messages.success(request, f"Product clone {new_product.asset_id} submitted for approval.")
        return redirect(redirect_url)




@login_required
def rental_list(request):
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'newest') # Default to newest
    billing_filter = request.GET.get('billing_day')

    # 1. Base Query (Optimized)
    rentals = Rental.objects.select_related('customer', 'asset', 'asset__type_of_asset').filter(status='ongoing')

    # 2. Advanced Search
    if query:
        rentals = rentals.filter(
            Q(customer__name__icontains=query) |
            Q(customer__phone_number_primary__icontains=query) |
            Q(customer__email__icontains=query) |
            Q(asset__asset_id__icontains=query) |
            Q(asset__serial_no__icontains=query) |
            Q(asset__brand__icontains=query) |
            Q(asset__model_no__icontains=query) |
            Q(asset__type_of_asset__name__icontains=query) | # NEW: Search "Laptop"
            Q(contract_number__icontains=query)
        )

    # 3. Billing Day Filter (Specific 1-31 filter)
    if billing_filter:
        rentals = rentals.filter(billing_day=billing_filter)

    # 4. Sorting Logic
    if sort_by == 'expiry':
        # Show expiring soonest first (exclude None values if needed)
        rentals = rentals.order_by('contract_validity')
    elif sort_by == 'billing':
        # Group by billing day (1, 2, 3...)
        rentals = rentals.order_by('billing_day')
    elif sort_by == 'customer':
        # A-Z Customer Name
        rentals = rentals.order_by('customer__name')
    elif sort_by == 'oldest':
        # Oldest rentals first
        rentals = rentals.order_by('rental_start_date')
    else:
        # Default: Newest rentals first
        rentals = rentals.order_by('-rental_start_date')

    return render(request, 'rentals/rental_list.html', {
        'rentals': rentals,
        'query': query,
        'sort_by': sort_by,
        'billing_filter': billing_filter,
        # Generate 1-31 list for the template dropdown
        'billing_days': range(1, 32)
    })

@login_required
def mark_rental_completed(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id)
    rental.status = 'completed'
    details = [f"Customer: {rental.customer.name}", f"Asset: {rental.asset.asset_id}"]

    log_action(
        request.user,
        "Marked rental as completed",
        "Rental",
        obj_id=rental.id,
        changes=details,
        object_repr=f"Rental {rental.id}"
    )
    rental.save()
    return redirect('rental_list')





@login_required
@user_passes_test(lambda u: u.is_superuser)
def report_dashboard(request):
    today = timezone.now().date()

    customers = Customer.objects.all()
    products = ProductAsset.objects.all()

    customer_id = request.GET.get('customer')
    product_id = request.GET.get('product')
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')
    customer_type = request.GET.get('customer_type')

    # Fetch all rentals
    rentals = Rental.objects.select_related('asset', 'customer').all()
    customer_business = []

    # Filter rentals based on customer type
    if customer_type == 'BNI':
        rentals = rentals.filter(customer__is_bni_member=True)
        selected_customers = Customer.objects.filter(is_bni_member=True)

    elif customer_type == 'Permanent':
        rentals = rentals.filter(customer__is_permanent=True)
        selected_customers = Customer.objects.filter(is_permanent=True)

    else:
        selected_customers = []


    # Replace your "Revenue by customer" and "customer_business" loops with this:
    customer_revenue = {}
    customer_business = []

    for customer in Customer.objects.all():
        customer_total = Decimal('0.00')
        # Get all rentals for this customer
        customer_rentals = Rental.objects.filter(customer=customer)

        for rental in customer_rentals:
            if not rental.rental_start_date:
                continue

            # Match calculator logic: use end_date or today
            end_date = rental.rental_end_date or today
            if end_date > today:
                end_date = today

            current_date = rental.rental_start_date
            rental_revenue = Decimal('0.00')

            # Month-by-month calculation (Exact match to your calculator)
            while current_date <= end_date:
                if current_date.month == 12:
                    next_month_start = date(current_date.year + 1, 1, 1)
                else:
                    next_month_start = date(current_date.year, current_date.month + 1, 1)

                days_in_month = (next_month_start - timedelta(days=1)).day

                if current_date.month == end_date.month and current_date.year == end_date.year:
                    end_day = end_date.day
                else:
                    end_day = days_in_month

                days_to_count = end_day - current_date.day + 1
                daily_rate = rental.payment_amount / Decimal(days_in_month)
                rental_revenue += (daily_rate * Decimal(days_to_count))
                current_date = next_month_start

            customer_total += rental_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Fill both data structures
        if customer_total > 0:
            customer_revenue[customer.name] = float(customer_total)
            customer_business.append({'name': customer.name, 'total': float(customer_total)})

    # If product selected, calculate profit
    product_obj = None
    if product_id:
        try:
            product_obj = ProductAsset.objects.get(id=product_id)
        except ProductAsset.DoesNotExist:
            product_obj = None

    gross_profit = maintenance_cost = net_profit = None
    sold_asset = 0.0

    if product_obj:
        # Calculate revenue and costs for this product
        purchase_price = float(product_obj.purchase_price or 0)
        gross_profit = float(product_obj.revenue or 0)

        if product_obj.condition_status == 'sold' and product_obj.sale_price:
            sold_asset = float(product_obj.sale_price or 0)

        # Repair cost
        repair_cost = Repair.objects.filter(product=product_obj).aggregate(total=Sum('cost'))['total'] or 0

        # Config cost
        config_cost = ProductConfiguration.objects.filter(asset=product_obj).aggregate(total=Sum('cost'))['total'] or 0

        maintenance_cost = float(repair_cost) + float(config_cost)
        # Add sold_asset to the gains
        net_profit = (gross_profit + sold_asset) - maintenance_cost - purchase_price

    # Apply filters
    if customer_id:
        rentals = rentals.filter(customer_id=customer_id)
    if product_id:
        rentals = rentals.filter(asset_id=product_id)
    if start:
        rentals = rentals.filter(rental_start_date__gte=parse_date(start))
    if end:
        rentals = rentals.filter(rental_start_date__lte=parse_date(end))

    # Total revenue directly from ProductAsset revenue
    total_revenue = ProductAsset.objects.aggregate(total=Sum('revenue'))['total'] or 0
    total_rentals = rentals.count()

    # Total rental days
    total_days = float(sum(
        (r.rental_end_date - r.rental_start_date).days
        for r in rentals if r.rental_end_date and r.rental_start_date
    ))

    # Monthly revenue trends
    # Replace your "Monthly revenue trends" loop with this:
    monthly = {}
    for r in rentals:
        if not r.rental_start_date: continue

        end_date = r.rental_end_date or today
        if end_date > today: end_date = today

        current_date = r.rental_start_date
        while current_date <= end_date:
            month_key = current_date.strftime("%Y-%m")

            # Calculate days in this specific month
            if current_date.month == 12:
                next_month = date(current_date.year + 1, 1, 1)
            else:
                next_month = date(current_date.year, current_date.month + 1, 1)

            days_in_month = (next_month - timedelta(days=1)).day

            if current_date.month == end_date.month and current_date.year == end_date.year:
                days_to_count = end_date.day - current_date.day + 1
            else:
                days_to_count = days_in_month - current_date.day + 1

            revenue_for_this_month = (r.payment_amount / Decimal(days_in_month)) * Decimal(days_to_count)

            # Add to the specific month in the chart
            monthly[month_key] = monthly.get(month_key, 0) + float(revenue_for_this_month)
            current_date = next_month
    # Top 5 assets by revenue
    top_assets = (
        ProductAsset.objects.annotate(total_income=Sum('revenue'))
        .filter(total_income__gt=0)
        .order_by('-total_income')[:5]
    )

    # Revenue by asset type
    type_revenue = defaultdict(float)
    for asset in ProductAsset.objects.prefetch_related('rentals'):
        asset_type = asset.type_of_asset.name if asset.type_of_asset else "Unknown"
        type_revenue[asset_type] += float(asset.revenue or 0)

    type_labels = list(type_revenue.keys())
    type_values = [float(v) for v in type_revenue.values()]


    sorted_customers = sorted(customer_revenue.items(), key=lambda x: x[1], reverse=True)
    customer_labels = [name for name, _ in sorted_customers]
    customer_values = [value for _, value in sorted_customers]


    top_repaired_assets = (
        Repair.objects.values('product__asset_id', 'product__brand', 'product__model_no')
        .annotate(total_repairs=Count('id'), total_cost=Sum('cost'))
        .order_by('-total_cost')[:5]
    )

    # today = timezone.now().date()
    in_warranty_assets = []
    for asset in products:
        if asset.purchase_date and asset.warranty_duration_months and asset.warranty_duration_months > 0:
            expiry_date = asset.purchase_date + relativedelta(months=asset.warranty_duration_months)
            if today <= expiry_date:
                in_warranty_assets.append({
                    "asset_id": asset.asset_id,
                    "brand": asset.brand,
                    "model_no": asset.model_no,
                    "expiry_date": expiry_date,
                    "days_left": (expiry_date - today).days
                })
    in_warranty_count = len(in_warranty_assets)


    # Repairs with active warranty
    # today = timezone.now().date()

    repairs = Repair.objects.all()
    repairs_with_warranty = []

    for r in repairs:
        expiry = r.repair_warranty_expiry_date  # use property method
        if expiry and today <= expiry:
            repairs_with_warranty.append(r)


    # Ensure all months between start and end exist, even with 0 revenue
    if monthly:
        all_keys = sorted(monthly.keys())
        first_month = datetime.strptime(all_keys[0], "%Y-%m")
        last_month = datetime.strptime(all_keys[-1], "%Y-%m")

        current = first_month
        while current <= last_month:
            key = current.strftime("%Y-%m")
            if key not in monthly:
                monthly[key] = 0.0

            # Increment month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)


    customer_assets = []
    if customer_id:
        # 1. Fetch assets rented by this customer
        customer_assets = ProductAsset.objects.filter(rentals__customer_id=customer_id).distinct()

        # 2. Calculate revenue specifically for this customer on these assets
        for asset in customer_assets:
            asset_total = Decimal('0.00')
            # Get rentals only for this specific asset AND this specific customer
            asset_rentals = Rental.objects.filter(asset=asset, customer_id=customer_id)

            for rental in asset_rentals:
                if not rental.rental_start_date:
                    continue

                # Use same date logic as your main report
                calc_end_date = rental.rental_end_date or today
                if calc_end_date > today:
                    calc_end_date = today

                # Skip invalid dates
                if rental.rental_start_date > calc_end_date:
                    continue

                # Calculate days and revenue
                current_date = rental.rental_start_date
                rental_rev = Decimal('0.00')

                while current_date <= calc_end_date:
                    if current_date.month == 12:
                        next_month = date(current_date.year + 1, 1, 1)
                    else:
                        next_month = date(current_date.year, current_date.month + 1, 1)

                    days_in_month = (next_month - timedelta(days=1)).day

                    if current_date.month == calc_end_date.month and current_date.year == calc_end_date.year:
                        end_day = calc_end_date.day
                    else:
                        end_day = days_in_month

                    days_to_count = end_day - current_date.day + 1
                    daily_rate = rental.payment_amount / Decimal(days_in_month)
                    rental_rev += (daily_rate * Decimal(days_to_count))

                    current_date = next_month

                asset_total += rental_rev

            # 3. Attach this calculated value to the asset object temporarily
            asset.customer_specific_revenue = asset_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    # --- END OF NEW BLOCK ---
    roi_percentage = 0
    total_cost = 0
    if product_obj:
        total_cost = purchase_price + maintenance_cost
        if purchase_price > 0:
            roi_percentage = (net_profit / purchase_price) * 100
    # # Now proceed to sort and dump to JSON as shown in step 1
    sorted_months = sorted(monthly.keys())
    # Final context
    context = {
        'customers': customers,
        'products': products,
        'rentals': rentals,

        'customer_assets': customer_assets,
        'roi_percentage': roi_percentage,  # <--- Add this
        'total_cost': total_cost,          # <--- Add this
        'total_revenue': total_revenue,
        'total_rentals': total_rentals,
        'purchase_price': product_obj.purchase_price if product_obj else 0,
        'gross_profit': gross_profit,
        'sold_asset': sold_asset,
        'maintenance_cost': maintenance_cost,
        "in_warranty_count": in_warranty_count,
        "in_warranty_assets": in_warranty_assets,


        "repairs_with_warranty":repairs_with_warranty,

        # Top repaired
        "top_repaired_assets": top_repaired_assets,

        'total_days': total_days,
        'net_profit': net_profit,
        'product_obj': product_obj,
        'product_id': product_id,
        'monthly_labels': json.dumps(sorted_months),
        'monthly_values': json.dumps([monthly[m] for m in sorted_months]),
        'top_assets': top_assets,
        'customer_business': customer_business,
        'type_labels': json.dumps(type_labels),
        'type_values': json.dumps(type_values),
        'customer_labels': json.dumps(customer_labels),
        'customer_values': json.dumps(customer_values),


    }

    return render(request, 'rentals/report_dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def run_revenue_calculator(request):
    """
    View to recalculate revenue for all rentals and update each product's total revenue.
    Accessible only to superusers.
    """
    today = date.today()

    # Step 1: Reset all revenues to 0
    ProductAsset.objects.update(revenue=Decimal('0.00'))

    updated_rentals = 0

    # Step 2: Get all rentals with valid payment amounts
    rentals = Rental.objects.filter(payment_amount__gt=0)

    for rental in rentals:
        # ✅ Skip rentals with missing start date
        if not rental.rental_start_date:
            print(f"Skipping rental {rental.id} - No start date")
            continue

        # ✅ Determine the effective end date
        end_date = rental.rental_end_date or today

        # Don't calculate beyond today
        if end_date > today:
            end_date = today

        # ✅ Skip if start date is after end date (invalid data)
        if rental.rental_start_date > end_date:
            print(f"Skipping rental {rental.id} - Start date after end date")
            continue

        total_rental_revenue = Decimal('0.00')
        current_date = rental.rental_start_date

        # Step 3: Loop through each month between start and end
        while current_date <= end_date:
            # Calculate days in current month
            if current_date.month == 12:
                next_month_start = date(current_date.year + 1, 1, 1)
            else:
                next_month_start = date(current_date.year, current_date.month + 1, 1)

            days_in_month = (next_month_start - timedelta(days=1)).day

            # Calculate end day for this segment
            if current_date.month == end_date.month and current_date.year == end_date.year:
                end_day = end_date.day
            else:
                end_day = days_in_month

            # Number of active days in this month
            days_to_count = end_day - current_date.day + 1

            # Keep full precision for daily rate
            daily_rate = rental.payment_amount / Decimal(days_in_month)

            # Add precise total, round at the very end
            total_rental_revenue += (daily_rate * Decimal(days_to_count))

            # Move to the first day of next month
            current_date = next_month_start

        # Round the final result once
        total_rental_revenue = total_rental_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


        # Step 4: Update the product's total revenue
        if rental.asset:
            before = rental.asset.revenue
            rental.asset.revenue += total_rental_revenue
            rental.asset.save(update_fields=['revenue'])

            updated_rentals += 1
            print(
                f"[{rental.asset.asset_id}] Before: {before} | Added: {total_rental_revenue} | After: {rental.asset.revenue}"
            )

    # Step 5: Display success message
    details = [f"Rentals Updated: {updated_rentals}", "Recalculated full revenue history"]
    log_action(
        request.user,
        "Ran revenue recalculation",
        "System Task",
        changes=details,
        object_repr="Revenue Calc"
    )
    messages.success(
        request,
        f"Revenue successfully recalculated for {updated_rentals} rentals as of {today}."
    )
    # query_string = request.GET.urlencode()
    # redirect_url = reverse('product_list')
    # if query_string:
    #     redirect_url += f'?{query_string}'
    return redirect('product_list')
      # Update with your actual reports dashboard URL




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
            supplier = form.save()
            details = [
                f"Name: {supplier.name}",
                f"GST: {supplier.gstin}",
                f"Phone: {supplier.phone_primary}"
            ]
            log_action(
                request.user,
                "Created new supplier",
                "Supplier",
                obj_id=supplier.id,
                changes=details,
                object_repr=supplier.name
            )
            messages.success(request, "Vendor added successfully.")
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'rentals/add_supplier.html', {'form': form})


@login_required
def edit_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    old_instance = Supplier.objects.get(pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            updated_supplier = form.save()

            # 2. Calculate Diff
            changes = get_changed_fields(old_instance, updated_supplier)

            # 3. Log
            log_action(
                request.user,
                "Edited supplier",
                "Supplier",
                obj_id=updated_supplier.id,
                changes=changes,
                object_repr=updated_supplier.name
            )
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
            subject="Rental Management System - Notification Billing Reminder",
            message=body,
            from_email='support@pixelitsolution.com',
            recipient_list=['accounts@pixelitsolution.com','aryanpore3056@gmail.com'],
            fail_silently=False,
            )

        count = rentals_due_today.count()
        details = [f"Reminders Sent: {count}", f"Date: {today}"]

        log_action(
            request.user,
            "Sent billing reminders",
            "System Task",
            changes=details,
            object_repr=f"Billing Reminder {today}"
        )
        messages.success(request, "Billing reminder sent successfully!")
    except Exception as e:
        messages.error(request, f"Failed to send reminder: {e}")


    return redirect('rental_list')

@login_required
def add_repair(request, pk):

    product = get_object_or_404(ProductAsset, pk=pk)
    # nameing = get(ProductAsset)

    if request.method == 'POST':
        form = RepairForm(request.POST)
        if form.is_valid():
            if request.user.is_superuser:
                # SUPERUSER → Directly save to main Repair table
                repair = form.save(commit=False)
                repair.edited_by = request.user

                # Link product properly
                form_product = form.cleaned_data.get("product")
                if not form_product and product:
                    repair.product = product

                repair.save()

                details = [f"Issue: {repair.name}", f"Cost: {repair.cost}", f"Date: {repair.date}"]
                log_action(
                    request.user,
                    "Added new repair",
                    "Repair",
                    obj_id=repair.id,
                    changes=details,
                    object_repr=f"Repair {repair.id} ({repair.product.asset_id})"
                )
                messages.success(request, "Repair added successfully.")
                return redirect('product_detail', pk=repair.product.pk)
            else:
                # NORMAL USER → Save to PendingRepair table
                cleaned_data = form.cleaned_data

                pending_repair = PendingRepair(
                    product=cleaned_data.get('product') or product,
                    name=cleaned_data.get('name'),
                    cost=cleaned_data.get('cost'),
                    date=cleaned_data.get('date'),
                    repair_warranty_months=cleaned_data.get('repair_warranty_months'),

                    submitted_by=request.user,
                    is_edit=False,  # NEW REPAIR, not an edit
                )
                pending_repair.save()
                details = [f"Issue: {pending_repair.name}", f"Est Cost: {pending_repair.cost}"]
                log_action(
                    request.user,
                    "Submitted repair for approval",
                    "PendingRepair",
                    obj_id=pending_repair.id,
                    changes=details,
                    object_repr=f"Req Repair {pending_repair.product.asset_id}"
                )
                messages.success(
                    request,
                    "Repair submitted for approval. It will appear after superuser approval."
                )
                return redirect('product_detail', pk=pending_repair.product.pk)
    else:
        form = RepairForm(initial={'product': product} if product else None)
        if product:
            # Lock product selection if we are adding repair for a specific product
            form.fields['product'].queryset = ProductAsset.objects.filter(id=product.id)
            form.fields['product'].widget.attrs['readonly'] = True  # optional disable

    return render(request, 'rentals/add_repair.html', {'form': form, 'product': product})


@login_required
def edit_repair(request, pk):
    repair = get_object_or_404(Repair, pk=pk)
    old_instance = Repair.objects.get(pk=pk)
    if request.user.is_superuser:
        # Superuser edits directly
        form = RepairForm(request.POST or None, instance=repair)
        if request.method == 'POST' and form.is_valid():
            updated_repair = form.save(commit=False)
            updated_repair.edited_by = request.user
            updated_repair.save()
            changes = get_changed_fields(old_instance, updated_repair)

            # 3. Log
            log_action(
                request.user,
                "Edited repair",
                "Repair",
                obj_id=updated_repair.id,
                changes=changes,
                object_repr=f"Repair for {updated_repair.product.asset_id}"
            )
            messages.success(request, "Repair updated successfully.")
            return redirect('product_detail', pk=repair.product.pk)

    else:
        # Normal user submits edit for approval
        if request.method == 'POST':
            form = RepairForm(request.POST, instance=repair)
            if form.is_valid():
                # Check if there is already a pending edit for this repair
                pending_repair = PendingRepair.objects.filter(
                    original_repair=repair,
                    is_edit=True
                ).first()

                if pending_repair:
                    # Update existing pending edit instead of creating duplicate
                    pending_repair.product=form.product
                    pending_repair.date = form.cleaned_data['date']
                    pending_repair.cost = form.cleaned_data['cost']
                    pending_repair.name = form.cleaned_data['name']
                    pending_repair.product = repair.product
                    pending_repair.submitted_by = request.user
                    pending_repair.save()
                    details = [f"Asset: {repair.product.asset_id}", "Updated existing edit request"]
                    log_action(
                        request.user,
                        "Updated pending repair request",
                        "PendingRepair",
                        obj_id=pending_repair.id,
                        changes=details,
                        object_repr=f"Req Repair {repair.product.asset_id}"
                    )
                    messages.success(request, "Repair edit updated and submitted for approval.")
                else:
                    # Create a new pending edit request
                    p =PendingRepair.objects.create(
                        original_repair=repair,
                        submitted_by=request.user,
                        date=form.cleaned_data['date'],
                        cost=form.cleaned_data['cost'],
                        name=form.cleaned_data['name'],
                        product=repair.product,
                        is_edit=True
                    )
                    changes = get_changed_fields(repair, p)
                    log_action(
                        request.user,
                        "Submitted repair edit for approval",
                        "PendingRepair",
                        obj_id=p.id,
                        changes=changes,
                        object_repr=f"Req Repair {repair.product.asset_id}"
                    )
                    messages.success(request, "Repair edit submitted for approval.")
                return redirect('product_detail', pk=repair.product.pk)
        else:
            form = RepairForm(instance=repair)

    return render(request, 'rentals/edit_repair.html', {'form': form, 'repair': repair})


@login_required
def delete_repair(request, pk):
    repair = get_object_or_404(Repair, pk=pk)
    product_pk = repair.product.pk  # Store this before potential deletion

    if request.user.is_superuser:
        # Superuser can delete directly
        details = [f"Issue: {repair.name}", f"Cost: {repair.cost}"]
        log_action(
            request.user,
            "Deleted repair",
            "Repair",
            obj_id=repair.id,
            changes=details,
            object_repr=f"Repair {repair.id}"
        )
        repair.delete()
        messages.success(request, "Repair deleted successfully.")
        return redirect('product_detail', pk=product_pk)

    else:
        # Normal user submits delete request for approval
        pending_repair = PendingRepair.objects.filter(
            original_repair=repair,
            is_edit=True
        ).first()

        if pending_repair:
            messages.warning(request, "Delete request already pending for this repair.")
        else:
            # Create a pending delete request (no data means delete)
            p = PendingRepair.objects.create(
                original_repair=repair,
                submitted_by=request.user,
                product=repair.product,
                is_edit=True,
                # Leave date, cost, name as None to indicate delete request
                date=None,
                cost=None,
                name=None
            )
            details = [f"Asset: {repair.product.asset_id}", f"Issue: {repair.name}", "Requested Deletion"]

            log_action(
                request.user,
                "Submitted repair delete request",
                "PendingRepair",
                obj_id=p.id,
                changes=details,
                object_repr=f"Req Delete Repair {repair.id}"
            )
            messages.success(request, "Delete request submitted for approval.")

        return redirect('product_detail', pk=product_pk)



@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_repair_edit(request, pk):
    pending_repair = get_object_or_404(PendingRepair, pk=pk)

    if request.user.is_superuser:
        if pending_repair.is_edit:
            # EDIT EXISTING REPAIR
            original = pending_repair.original_repair
            changes = get_changed_fields(original, pending_repair)
            original.name = pending_repair.name
            original.cost = pending_repair.cost
            original.date = pending_repair.date
            original.edited_by = pending_repair.submitted_by
            # original.edited_at = timezone.now()
            original.save()
            log_action(
                request.user,
                "Approved Repair Edit",
                "Repair",
                obj_id=original.id,
                changes=changes,
                object_repr=f"Repair {original.id}"
            )
            messages.success(request, "Repair edit approved successfully.")
        else:
            # CREATE NEW REPAIR
            new_repair = Repair.objects.create(
                product=pending_repair.product,
                name=pending_repair.name,
                cost=pending_repair.cost,
                date=pending_repair.date,
                edited_by=pending_repair.submitted_by,
                edited_at=pending_repair.submitted_at
            )
            details = [f"Asset: {new_repair.product.asset_id}", f"Cost: {new_repair.cost}"]
            log_action(
                request.user,
                "Approved New Repair",
                "Repair",
                obj_id=new_repair.id,
                changes=details,
                object_repr=f"Repair {new_repair.id}"
            )
            messages.success(request, "New repair approved successfully.")
        # DELETE the pending record after approval
        pending_repair.delete()

    return redirect('approval_dashboard')

@login_required
def settings_home(request):
    return render(request, 'rentals/settings.html')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def manage_hdd_Options(request):
    items = HDDOption.objects.all()
    editing = False
    instance = None

    if request.GET.get("edit"):
        instance = get_object_or_404(HDDOption, id=request.GET["edit"])
        editing = True

    old_instance = HDDOption.objects.get(id=instance.id) if instance else None

    form = HDDOptionForm(request.POST or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        obj = form.save()

        if old_instance:
            # Edit Mode
            changes = get_changed_fields(old_instance, obj)
            action = "Edited HDD Option"
        else:
            # Create Mode
            changes = [f"Name: {obj.name}"] # Assuming 'name' is the field
            action = "Created HDD Option"

        log_action(
            request.user,
            action,
            "HDDOption",
            obj_id=obj.id,
            changes=changes,
            object_repr=str(obj)
        )
        return redirect('manage_hdd_Options')

    return render(request, 'rentals/manage_Options.html', {
        'form': form,
        'items': items,
        'field_name': 'HDD',
        'title': 'HDD',
        'editing': editing,
        'current_view': 'manage_hdd_Options',
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def manage_ram_Options(request):
    items = RAMOption.objects.all()
    editing = False
    instance = None

    if request.GET.get("edit"):
        instance = get_object_or_404(RAMOption, id=request.GET["edit"])
        editing = True

    form = RAMOptionForm(request.POST or None, instance=instance)

    old_instance = RAMOption.objects.get(id=instance.id) if instance else None

    if request.method == 'POST' and form.is_valid():
        updated_ram_option = form.save()

        if old_instance:
            changes = get_changed_fields(old_instance, updated_ram_option)
            action = "Edited RAM Option"
        else:
            changes = [f"Name: {updated_ram_option.name}"]
            action = "Created RAM Option"

        log_action(
            request.user,
            action,
            "RAMOption",
            obj_id=updated_ram_option.id,
            changes=changes,
            object_repr=str(updated_ram_option)
        )
        return redirect('manage_ram_Options')

    return render(request, 'rentals/manage_Options.html', {
        'form': form,
        'items': items,
        'field_name': 'RAM',
        'title': 'RAM',
        'editing': editing,
        'current_view': 'manage_ram_Options',
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def manage_cpu_Options(request):
    items = CPUOption.objects.all()
    editing = False
    instance = None

    if request.GET.get("edit"):
        instance = get_object_or_404(CPUOption, id=request.GET["edit"])
        editing = True

    form = CPUOptionForm(request.POST or None, instance=instance)
    old_instance = CPUOption.objects.get(id=instance.id) if instance else None
    if request.method == 'POST' and form.is_valid():
        updated_cpu_option = form.save()

        if old_instance:
            changes = get_changed_fields(old_instance, updated_cpu_option)
            action = "Edited CPU Option"
        else:
            changes = [f"Name: {updated_cpu_option.name}"]
            action = "Created CPU Option"

        log_action(
            request.user,
            action,
            "CPUOption",
            obj_id=updated_cpu_option.id,
            changes=changes,
            object_repr=str(updated_cpu_option)
        )
        return redirect('manage_cpu_Options')

    return render(request, 'rentals/manage_Options.html', {
        'form': form,
        'items': items,
        'field_name': 'CPU',
        'title': 'CPU',
        'editing': editing,
        'current_view': 'manage_cpu_Options',
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def manage_display_size_Options(request):
    items = DisplaySizeOption.objects.all()
    editing = False
    instance = None

    if request.GET.get("edit"):
        instance = get_object_or_404(DisplaySizeOption, id=request.GET["edit"])
        editing = True

    form = DisplaySizeOptionForm(request.POST or None, instance=instance)
    old_instance = DisplaySizeOption.objects.get(id=instance.id) if instance else None
    if request.method == 'POST' and form.is_valid():
        updated_display_size_option = form.save()

        if old_instance:
            changes = get_changed_fields(old_instance, updated_display_size_option)
            action = "Edited Display Size Option"
        else:
            changes = [f"Name: {updated_display_size_option.name}"]
            action = "Created Display Size Option"

        log_action(
            request.user,
            action,
            "DisplaySizeOption",
            obj_id=updated_display_size_option.id,
            changes=changes,
            object_repr=str(updated_display_size_option)
        )
        return redirect('manage_display_size_Options')

    return render(request, 'rentals/manage_Options.html', {
        'form': form,
        'items': items,
        'field_name': 'Display Size',
        'title': 'Display Size',
        'editing': editing,
        'current_view': 'manage_display_size_Options',
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def manage_graphics_Options(request):
    items =GraphicsOption.objects.all()
    editing = False
    instance = None

    if request.GET.get("edit"):
        instance = get_object_or_404(GraphicsOption, id=request.GET["edit"])
        editing = True

    form = GraphicsOptionForm(request.POST or None, instance=instance)
    old_instance = GraphicsOption.objects.get(id=instance.id) if instance else None

    if request.method == 'POST' and form.is_valid():


        updated_graphics_option = form.save()

        if old_instance:
            changes = get_changed_fields(old_instance, updated_graphics_option)
            action = "Edited Graphics Option"
        else:
            changes = [f"Name: {updated_graphics_option.name}"]
            action = "Created Graphics Option"

        log_action(
            request.user,
            action,
            "GraphicsOption",
            obj_id=updated_graphics_option.id,
            changes=changes,
            object_repr=str(updated_graphics_option)
        )
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
    old_instance = ProductConfiguration.objects.get(id=config_id)

    if request.user.is_superuser:
        form = ProductConfigurationForm(request.POST or None, instance=config)
        if request.method == 'POST' and form.is_valid():
            updated_config = form.save()

            # 2. Diff
            changes = get_changed_fields(old_instance, updated_config)

            # 3. Log
            log_action(
                request.user,
                "Edited product configuration",
                "ProductConfiguration",
                obj_id=config.id,
                changes=changes,
                object_repr=f"Config for {config.asset.asset_id}"
            )
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
                pending.save() # Save first to generate ID

                # FIX: Calculate Diff between Original and Requested
                changes = get_changed_fields(config, pending)

                log_action(
                    request.user,
                    "Requested Config Edit",
                    "PendingProductConfiguration",
                    obj_id=pending.id,
                    changes=changes,
                    object_repr=f"Req Config {config.asset.asset_id}"
                )
                messages.success(request, "Configuration edit submitted for approval.")
                return redirect('product_detail', pk=config.asset.pk)
        else:
            form = ProductConfigurationForm(instance=config)

    return render(request, 'rentals/edit_config.html', {'form': form, 'config': config})





@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_edited_config(request, pk):
    pending = get_object_or_404(PendingProductConfiguration, pk=pk)
    config = pending.original_config

    changes = get_changed_fields(config, pending)

    # Apply changes
    config.ram = pending.ram
    config.hdd = pending.hdd
    config.ssd = pending.ssd
    config.graphics = pending.graphics
    config.display_size = pending.display_size
    config.power_supply = pending.power_supply
    config.detailed_config = pending.detailed_config
    config.save()

    log_action(
        request.user,
        "Approved Config Edit",
        "ProductConfiguration",
        obj_id=config.id,
        changes=changes,
        object_repr=f"Config {config.id}"
    )
    pending.delete()
    messages.success(request, "Configuration update approved.")
    return redirect('approval_dashboard')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_edited_config(request, pk):
    pending = get_object_or_404(PendingProductConfiguration, pk=pk)

    details = [f"Asset: {pending.asset.asset_id}", "Rejected Edit Request"]

    log_action(
        request.user,
        "Rejected config edit",
        "PendingProductConfiguration",
        obj_id=pending.id,
        changes=details,
        object_repr=f"Req Edit {pending.asset.asset_id}"
    )
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
    details = [f"Asset: {pending.product.asset_id}", f"Issue: {pending.name}", "Rejected Edit"]

    log_action(
        request.user,
        "Rejected repair edit",
        "PendingRepair",
        obj_id=pending.id,
        changes=details,
        object_repr=f"Req Edit Repair {pending.product.asset_id}"
    )
    pending.delete()
    messages.success(request, "Repair update approved.")
    return redirect('approval_dashboard')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_edited_repair(request, pk):
    pending = get_object_or_404(PendingRepair, pk=pk)

    details = [f"Asset: {pending.product.asset_id}", f"Issue: {pending.name}", "Rejected Edit"]

    log_action(
        request.user,
        "Rejected repair edit",
        "PendingRepair",
        obj_id=pending.id,
        changes=details,
        object_repr=f"Req Edit Repair {pending.product.asset_id}"
    )
    pending.delete()
    messages.info(request, "Repair update rejected.")
    return redirect('approval_dashboard')


@login_required
def check_contracts(request):
    today = now().date()

    # 1. Fetch expired rentals
    expired_rentals = Rental.objects.filter(
        contract_validity__isnull=False,
        contract_validity__lt=today,
        status="ongoing",
    )

    # 2. Check if we actually have any expired rentals
    if expired_rentals.exists():

        # 3. Build the email body
        body_lines = []
        for rental in expired_rentals:
            asset_id = rental.asset.asset_id if rental.asset else 'Unknown'
            customer_name = rental.customer.name if rental.customer else 'Unknown Customer'
            expiry_date = rental.contract_validity
            body_lines.append(f"- {asset_id} | {customer_name} | Expired: {expiry_date}")

        body = "⚠️ Contract Expiry Alert ({expired_rentals.count()} items)\nThe following contracts have expired:\n\n" + "\n".join(body_lines)

        # 4. Send Email to ADMINS (No need to check customer email)
        try:
            send_mail(
                subject=f"Rental Management System - Contract Notification",
                message=body,
                from_email='support@pixelitsolution.com',
                recipient_list=[
                    'accounts@pixelitsolution.com',
                    'support@pixelitsolution.com',
                    'rental@pixelitsolution.com',
                    'aryanpore3056@gmail.com'
                ],
                fail_silently=False,
            )
            messages.success(request, f"✅ Alert sent for {expired_rentals.count()} expired contracts.")
        except Exception as e:
            messages.error(request, f"❌ Failed to send email: {e}")

    else:
        messages.info(request, "👍 No expired contracts found today.")

    return redirect("rental_list")

class CustomerAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Customer.objects.all()
        if self.q:
            qs = qs.filter(
                Q(name__icontains=self.q) |
                Q(phone_number_primary__icontains=self.q) |
                Q(email__icontains=self.q)
            )
        return qs

    def get_result_label(self, item):
        return f"{item.name} - {item.phone_number_primary}"




# ----------------------------
# Helper: serialize querysets
# ----------------------------

def safe_serialize(obj):
    """Return dict of all public model fields safely"""
    data = {}
    for field in obj._meta.get_fields():
        if not hasattr(field, 'attname'):
            continue
        name = field.name
        value = getattr(obj, name, None)

        # Handle related objects (show readable name)
        if hasattr(value, "name"):
            value = value.name
        elif hasattr(value, "asset_id"):
            value = value.asset_id
        elif hasattr(value, "username"):
            value = value.username

        # Convert decimals, datetimes, etc.
        if value is None:
            data[name] = None
        elif hasattr(value, "isoformat"):
            try:
                data[name] = value.isoformat()
            except Exception:
                data[name] = str(value)
        else:
            data[name] = str(value)
    return data

def serialize_product(asset):
    """Return dict with full product details (flattened)."""
    return {
        'id': asset.id,
        'asset_id': asset.asset_id,
        'type_of_asset': asset.type_of_asset.name if asset.type_of_asset else None,
        'brand': asset.brand,
        'model_no': asset.model_no,
        'serial_no': asset.serial_no,
        'asset_number': asset.asset_number,
        'asset_suffix': asset.asset_suffix,
        'purchase_date': asset.purchase_date,
        'purchase_price': float(asset.purchase_price) if asset.purchase_price is not None else None,
        'current_value': float(asset.current_value) if asset.current_value is not None else None,
        'under_warranty': asset.under_warranty,
        'warranty_duration_months': asset.warranty_duration_months,
        'warranty_expiry_date': asset.warranty_expiry_date,
        'purchased_from': asset.purchased_from.name if asset.purchased_from else None,
        'condition_status': asset.condition_status,
        'sold_to': asset.sold_to,
        'sale_price': float(asset.sale_price) if asset.sale_price is not None else None,
        'sale_date': asset.sale_date,
        'date_marked_dead': asset.date_marked_dead,
        'damage_narration': asset.damage_narration,
        'revenue': float(asset.revenue) if asset.revenue is not None else 0.0,
        'edited_by': asset.edited_by.username if asset.edited_by else None,
        'edited_at': asset.edited_at,
        'total_repairs': float(asset.total_repairs) if hasattr(asset, 'total_repairs') else None,
        'total_rent_earned': float(asset.total_rent_earned) if hasattr(asset, 'total_rent_earned') else None,
    }

def serialize_pending_product(p):
    return {
        'id': p.id,
        'pending_type': p.pending_type,
        'original_product_id': p.original_product.id if p.original_product else None,
        'asset_id': p.asset_id,
        'type_of_asset': p.type_of_asset.name if p.type_of_asset else None,
        'brand': p.brand,
        'model_no': p.model_no,
        'serial_no': p.serial_no,
        'asset_number': p.asset_number,
        'purchase_date': p.purchase_date,
        'purchase_price': float(p.purchase_price) if p.purchase_price is not None else None,
        'current_value': float(p.current_value) if p.current_value is not None else None,
        'under_warranty': p.under_warranty,
        'warranty_duration_months': p.warranty_duration_months,
        'purchased_from': p.purchased_from.name if p.purchased_from else None,
        'condition_status': p.condition_status,
        'submitted_by': p.submitted_by.username if p.submitted_by else None,
        'submitted_at': p.submitted_at,
        'sold_to': p.sold_to,
        'sale_price': float(p.sale_price) if p.sale_price is not None else None,
        'sale_date': p.sale_date,
    }

def serialize_configuration(cfg):
    return {
        'id': cfg.id,
        'asset_id': cfg.asset.asset_id if cfg.asset else None,
        'date_of_config': cfg.date_of_config,
        'cpu': cfg.cpu.name if cfg.cpu else None,
        'ram': cfg.ram.name if cfg.ram else None,
        'hdd': cfg.hdd.name if cfg.hdd else None,
        'ssd': cfg.ssd,
        'graphics': cfg.graphics.name if cfg.graphics else None,
        'display_size': cfg.display_size.name if cfg.display_size else None,
        'power_supply': cfg.power_supply,
        'cost': float(cfg.cost) if cfg.cost is not None else None,
        'edited_by': cfg.edited_by.username if cfg.edited_by else None,
        'edited_at': cfg.edited_at,
    }

def serialize_customer(c):
    return {
        'id': c.id,
        'name': c.name,
        'email': c.email,
        'phone_number_primary': c.phone_number_primary,
        'phone_number_secondary': c.phone_number_secondary,
        'address_primary': c.address_primary,
        'address_secondary': c.address_secondary,
        'is_permanent': c.is_permanent,
        'is_bni_member': c.is_bni_member,
        'reference_name': c.reference_name,
        'edited_by': c.edited_by.username if c.edited_by else None,
        'edited_at': c.edited_at,
    }

def serialize_rental(r):
    return {
        'id': r.id,
        'customer': r.customer.name if r.customer else None,
        'asset_id': r.asset.asset_id if r.asset else None,
        'rental_start_date': r.rental_start_date,
        'rental_end_date': r.rental_end_date,
        'billing_day': r.billing_day,
        'status': r.status,
        'payment_amount': float(r.payment_amount) if r.payment_amount is not None else None,
        'contract_number': r.contract_number,
        'contract_validity': r.contract_validity,
        'edited_by': r.edited_by.username if r.edited_by else None,
        'edited_at': r.edited_at,
    }

def serialize_repair(rep):
    return {
        'id': rep.id,
        'product_asset_id': rep.product.asset_id if rep.product else None,
        'name': rep.name,
        'date': rep.date,
        'cost': float(rep.cost) if rep.cost is not None else None,
        'info': rep.info,
        'repair_warranty_months': rep.repair_warranty_months,
        'under_repair_warranty': rep.under_repair_warranty,
        'edited_by': rep.edited_by.username if rep.edited_by else None,
        'edited_at': rep.edited_at,
    }

def serialize_supplier(s):
    return {
        'id': s.id,
        'name': s.name,
        'gstin': s.gstin,
        'address_primary': s.address_primary,
        'address_secondary': s.address_secondary,
        'phone_primary': s.phone_primary,
        'phone_secondary': s.phone_secondary,
        'email': s.email,
        'reference_name': s.reference_name,
    }

# ----------------------------
# CSV -> ZIP
# ----------------------------
@login_required
@user_passes_test(lambda u: u.is_superuser)
def export_reports_csv(request):
    """Export all data models to a ZIP of CSVs"""
    output = BytesIO()

    def write_csv_to_zip(zip_file, filename, queryset):
        if not queryset.exists():
            return
        rows = [safe_serialize(obj) for obj in queryset]
        csv_buffer = StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        zip_file.writestr(filename, csv_buffer.getvalue().encode('utf-8'))

    with ZipFile(output, 'w') as zip_file:
        write_csv_to_zip(zip_file, "customers.csv", Customer.objects.all())
        write_csv_to_zip(zip_file, "pending_customers.csv", PendingCustomer.objects.all())
        write_csv_to_zip(zip_file, "suppliers.csv", Supplier.objects.all())
        write_csv_to_zip(zip_file, "asset_types.csv", AssetType.objects.all())
        write_csv_to_zip(zip_file, "cpu_options.csv", CPUOption.objects.all())
        write_csv_to_zip(zip_file, "ram_options.csv", RAMOption.objects.all())
        write_csv_to_zip(zip_file, "hdd_options.csv", HDDOption.objects.all())
        write_csv_to_zip(zip_file, "graphics_options.csv", GraphicsOption.objects.all())
        write_csv_to_zip(zip_file, "display_size_options.csv", DisplaySizeOption.objects.all())
        write_csv_to_zip(zip_file, "products.csv", ProductAsset.objects.select_related('type_of_asset', 'purchased_from', 'edited_by'))
        write_csv_to_zip(zip_file, "pending_products.csv", PendingProduct.objects.select_related('type_of_asset', 'purchased_from', 'submitted_by'))
        write_csv_to_zip(zip_file, "configurations.csv", ProductConfiguration.objects.select_related('asset', 'cpu', 'ram', 'hdd', 'graphics', 'display_size', 'edited_by'))
        write_csv_to_zip(zip_file, "pending_configurations.csv", PendingProductConfiguration.objects.select_related('asset', 'cpu', 'ram', 'hdd', 'graphics', 'display_size', 'submitted_by'))
        write_csv_to_zip(zip_file, "rentals.csv", Rental.objects.select_related('customer', 'asset', 'edited_by'))
        write_csv_to_zip(zip_file, "pending_rentals.csv", PendingRental.objects.select_related('customer', 'asset', 'submitted_by'))
        write_csv_to_zip(zip_file, "repairs.csv", Repair.objects.select_related('product', 'edited_by'))
        write_csv_to_zip(zip_file, "pending_repairs.csv", PendingRepair.objects.select_related('product', 'submitted_by'))

    response = HttpResponse(output.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="full_report.zip"'
    log_action(
        request.user,
        "Exported full report",
        "Report Export",
        changes=["Format: CSV ZIP", "Scope: All Data"],
        object_repr="Full CSV Export"
    )
    return response

# -------------------------------------------
# Excel Export (Multi-sheet)
# -------------------------------------------
@login_required
@user_passes_test(lambda u: u.is_superuser)
def export_reports_excel(request):
    """Export all data models to a single Excel workbook"""
    output = BytesIO()

    def write_df(writer, sheet_name, queryset):
        if not queryset.exists():
            return
        data = [safe_serialize(obj) for obj in queryset]
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name=sheet_name[:30], index=False)

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        write_df(writer, 'Customers', Customer.objects.all())
        write_df(writer, 'PendingCustomers', PendingCustomer.objects.all())
        write_df(writer, 'Suppliers', Supplier.objects.all())
        write_df(writer, 'AssetTypes', AssetType.objects.all())
        write_df(writer, 'CPUOptions', CPUOption.objects.all())
        write_df(writer, 'RAMOptions', RAMOption.objects.all())
        write_df(writer, 'HDDOptions', HDDOption.objects.all())
        write_df(writer, 'GraphicsOptions', GraphicsOption.objects.all())
        write_df(writer, 'DisplaySizeOptions', DisplaySizeOption.objects.all())
        write_df(writer, 'Products', ProductAsset.objects.select_related('type_of_asset', 'purchased_from', 'edited_by'))
        write_df(writer, 'PendingProducts', PendingProduct.objects.select_related('type_of_asset', 'purchased_from', 'submitted_by'))
        write_df(writer, 'Configurations', ProductConfiguration.objects.select_related('asset', 'cpu', 'ram', 'hdd', 'graphics', 'display_size', 'edited_by'))
        write_df(writer, 'PendingConfigurations', PendingProductConfiguration.objects.select_related('asset', 'cpu', 'ram', 'hdd', 'graphics', 'display_size', 'submitted_by'))
        write_df(writer, 'Rentals', Rental.objects.select_related('customer', 'asset', 'edited_by'))
        write_df(writer, 'PendingRentals', PendingRental.objects.select_related('customer', 'asset', 'submitted_by'))
        write_df(writer, 'Repairs', Repair.objects.select_related('product', 'edited_by'))
        write_df(writer, 'PendingRepairs', PendingRepair.objects.select_related('product', 'submitted_by'))

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="full_report.xlsx"'
    response.write(output.getvalue())
    log_action(
        request.user,
        "Exported full report",
        "Report Export",
        changes=["Format: Excel", "Scope: All Data"],
        object_repr="Full Excel Export"
    )
    return response
# ----------------------------
# PDF export
# ----------------------------
@login_required
@user_passes_test(lambda u: u.is_superuser)
def export_reports_pdf(request):
    """
    Create a structured, unclipped PDF containing all key datasets.
    """
    output = BytesIO()
    # Use landscape orientation for more horizontal space
    doc = SimpleDocTemplate(output, pagesize=landscape(A4),
                            leftMargin=20, rightMargin=20,
                            topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        spaceAfter=10,
        textColor=colors.HexColor("#2E3A59")
    )

    normal_style = ParagraphStyle(
        'NormalSmall',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
    )

    def add_section(title, queryset):
        """Adds a formatted table for a queryset to the PDF"""
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 4))

        if not queryset.exists():
            elements.append(Paragraph("No data available", normal_style))
            elements.append(Spacer(1, 12))
            return

        # Serialize objects safely
        data = [safe_serialize(obj) for obj in queryset]

        # Prepare headers + rows
        headers = list(data[0].keys())
        table_data = [headers]
        for row in data:
            row_values = [Paragraph(str(row.get(h, "")), normal_style) for h in headers]
            table_data.append(row_values)

        # Adjust column widths dynamically
        col_count = len(headers)
        max_table_width = 10.5 * inch  # roughly landscape A4 usable width
        col_width = max_table_width / max(1, col_count)
        col_widths = [col_width] * col_count

        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E0E0E0")),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('WORDWRAP', (0, 0), (-1, -1), True),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 16))

    # ---- Sections ----
    add_section("Customers", Customer.objects.all())
    add_section("Pending Customers", PendingCustomer.objects.all())
    add_section("Suppliers", Supplier.objects.all())
    add_section("Asset Types", AssetType.objects.all())
    add_section("CPU Options", CPUOption.objects.all())
    add_section("RAM Options", RAMOption.objects.all())
    add_section("HDD Options", HDDOption.objects.all())
    add_section("Graphics Options", GraphicsOption.objects.all())
    add_section("Display Size Options", DisplaySizeOption.objects.all())
    add_section("Products", ProductAsset.objects.select_related('type_of_asset', 'purchased_from', 'edited_by'))
    add_section("Pending Products", PendingProduct.objects.select_related('type_of_asset', 'purchased_from', 'submitted_by'))
    add_section("Configurations", ProductConfiguration.objects.select_related('asset', 'cpu', 'ram', 'hdd', 'graphics', 'display_size', 'edited_by'))
    add_section("Pending Configurations", PendingProductConfiguration.objects.select_related('asset', 'cpu', 'ram', 'hdd', 'graphics', 'display_size', 'submitted_by'))
    add_section("Rentals", Rental.objects.select_related('customer', 'asset', 'edited_by'))
    add_section("Pending Rentals", PendingRental.objects.select_related('customer', 'asset', 'submitted_by'))
    add_section("Repairs", Repair.objects.select_related('product', 'edited_by'))
    add_section("Pending Repairs", PendingRepair.objects.select_related('product', 'submitted_by'))

    # Build PDF
    doc.build(elements)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="full_report.pdf"'
    response.write(output.getvalue())

    log_action(
        request.user,
        "Exported full report",
        "Report Export",
        changes=["Format: PDF", "Scope: All Data"],
        object_repr="Full PDF Export"
    )
    return response


@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_rental(request, pk):
    # Fetch the rental or return 404 if not found
    rental = get_object_or_404(Rental, pk=pk)

    # Capture details for the log before deletion
    customer_name = rental.customer.name if rental.customer else "Unknown"
    asset_id = rental.asset.asset_id if rental.asset else "N/A"

    # Log the action (Highly recommended based on your instructions)
    log_action(
        request.user,
        "Deleted Rental Record",
        "Rental",
        obj_id=pk,
        changes=[f"Customer: {customer_name}", f"Asset: {asset_id}"],
        object_repr=f"Rental {pk}"
    )

    # Perform the deletion
    rental.delete()

    # Add a success message for the UI
    messages.success(request, f"Rental for {customer_name} has been deleted.")

    # Redirect back to the history or list page
    return redirect('rental_history')

from django.db.models import Count
from .models import Customer, ProductAsset, Rental
from django.db.models import Count, Q

@login_required
@user_passes_test(lambda u: u.is_superuser)
def global_duplicate_checker(request):
    # 1. Duplicate Customers (Same name and phone)
    customer_dups = Customer.objects.values('name', 'phone_number_primary') \
        .annotate(count=Count('id')) \
        .filter(count__gt=1)

    # 2. Duplicate Products (Same Serial - exclude empty/null)
    product_dups = ProductAsset.objects.exclude(Q(serial_no__isnull=True) | Q(serial_no='')) \
        .values('serial_no') \
        .annotate(count=Count('id')) \
        .filter(count__gt=1)

    # 3. Duplicate Rentals (Grouped for Resolution)
    # Using asset__asset_id and customer__name to pass as URL parameters later
    rental_dups = Rental.objects.values(
        'customer__name',
        'asset__asset_id',
        'rental_start_date'
    ).annotate(count=Count('id')).filter(count__gt=1)

    context = {
        'customer_dups': customer_dups,
        'product_dups': product_dups,
        'rental_dups': rental_dups,
    }
    return render(request, 'rentals/global_duplicate_checker.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def resolve_duplicates(request):
    asset_id = request.GET.get('asset_id')
    customer_name = request.GET.get('customer')
    start_date = request.GET.get('start_date')

    # Optimized query with select_related to reduce DB hits
    rentals = Rental.objects.select_related('customer', 'asset', 'edited_by').all()

    if asset_id and customer_name and start_date:
        rentals = rentals.filter(
            asset__asset_id=asset_id,
            customer__name=customer_name,
            rental_start_date=start_date
        )
    else:
        # If accessed without params, redirect back
        return redirect('global_duplicate_checker')

    context = {
        'rentals': rentals,
        'asset_id': asset_id,
        'customer_name': customer_name,
        'start_date': start_date,
    }
    return render(request, 'rentals/resolve_duplicates.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def resolve_duplicates(request):
    # Parameters for Rental Duplicates
    asset_id = request.GET.get('asset_id')
    customer_name = request.GET.get('customer')
    start_date = request.GET.get('start_date')

    # Parameter for Product Duplicates
    serial_no = request.GET.get('serial_no')

    rentals = None
    products = None

    # Handle Product Duplicate Resolution
    if serial_no:
        products = ProductAsset.objects.filter(serial_no=serial_no).select_related('type_of_asset', 'purchased_from')
        context = {
            'products': products,
            'serial_no': serial_no,
            'mode': 'product'
        }
    # Handle Rental Duplicate Resolution
    elif asset_id and customer_name and start_date:
        rentals = Rental.objects.select_related('customer', 'asset', 'edited_by').filter(
            asset__asset_id=asset_id,
            customer__name=customer_name,
            rental_start_date=start_date
        )
        context = {
            'rentals': rentals,
            'asset_id': asset_id,
            'customer_name': customer_name,
            'start_date': start_date,
            'mode': 'rental'
        }
    else:
        return redirect('global_duplicate_checker')

    return render(request, 'rentals/resolve_duplicates.html', context)