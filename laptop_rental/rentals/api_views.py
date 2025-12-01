from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date

# --- IMPORTS FROM YOUR APP ---
from .models import (
    Customer, ProductAsset, Rental, Repair, ProductConfiguration,
    PendingCustomer, PendingProduct, PendingRental, PendingRepair, PendingProductConfiguration,
    AssetType, CPUOption, RAMOption, HDDOption, GraphicsOption, DisplaySizeOption
)
from .serializers import (
    # Read/Write
    CustomerSerializer, ProductAssetSerializer, RentalSerializer, RepairSerializer,
    ProductConfigurationSerializer,
    # Options
    AssetTypeSerializer, CPUOptionSerializer, RAMOptionSerializer, HDDOptionSerializer,
    GraphicsOptionSerializer, DisplaySizeOptionSerializer,
    # Pending
    PendingCustomerSerializer, PendingProductSerializer, PendingRentalSerializer,
    PendingRepairSerializer, PendingConfigSerializer
)

# ===================================================================
# 1. AUTHENTICATION
# ===================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "is_superuser": user.is_superuser,
            "username": user.username
        })
    return Response({"error": "Invalid Credentials"}, status=400)


# ===================================================================
# 2. DROPDOWN OPTIONS (Read Only)
# ===================================================================
# These ViewSets just provide lists for your dropdown menus
class OptionViewSetMixin(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = None # Dropdowns don't need pagination

class AssetTypeViewSet(OptionViewSetMixin):
    queryset = AssetType.objects.all()
    serializer_class = AssetTypeSerializer

class CPUViewSet(OptionViewSetMixin):
    queryset = CPUOption.objects.all()
    serializer_class = CPUOptionSerializer

class RAMViewSet(OptionViewSetMixin):
    queryset = RAMOption.objects.all()
    serializer_class = RAMOptionSerializer

class HDDViewSet(OptionViewSetMixin):
    queryset = HDDOption.objects.all()
    serializer_class = HDDOptionSerializer

class GraphicsViewSet(OptionViewSetMixin):
    queryset = GraphicsOption.objects.all()
    serializer_class = GraphicsOptionSerializer

class DisplayViewSet(OptionViewSetMixin):
    queryset = DisplaySizeOption.objects.all()
    serializer_class = DisplaySizeOptionSerializer


# ===================================================================
# 3. MAIN LOGIC VIEWSETS (The Heavy Lifters)
# ===================================================================

class ProductAssetViewSet(viewsets.ModelViewSet):
    queryset = ProductAsset.objects.all().order_by('asset_id')
    serializer_class = ProductAssetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Replicates search and date filtering from views.py"""
        qs = super().get_queryset()
        query = self.request.query_params.get('q')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        asset_type = self.request.query_params.get('type')

        if query:
            qs = qs.filter(
                Q(asset_id__icontains=query) |
                Q(brand__icontains=query) |
                Q(model_no__icontains=query) |
                Q(serial_no__icontains=query)
            )
        if start_date:
            qs = qs.filter(purchase_date__gte=parse_date(start_date))
        if end_date:
            qs = qs.filter(purchase_date__lte=parse_date(end_date))
        if asset_type:
            qs = qs.filter(type_of_asset__id=asset_type)
            
        return qs

    def create(self, request, *args, **kwargs):
        """Intercepts SAVE to handle Pending logic"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if request.user.is_superuser:
            # Superuser -> Save Directly
            serializer.save(edited_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # Normal User -> Save to PendingProduct
            data = serializer.validated_data
            PendingProduct.objects.create(
                submitted_by=request.user,
                pending_type='add',
                # Manually map fields from validated_data to Pending model
                type_of_asset=data['type_of_asset'],
                brand=data['brand'],
                model_no=data['model_no'],
                serial_no=data.get('serial_no'),
                purchase_price=data['purchase_price'],
                current_value=data['current_value'],
                purchase_date=data['purchase_date'],
                condition_status=data['condition_status'],
                asset_id=data.get('asset_id', ''),
                # Add other fields as necessary
            )
            return Response({"message": "Submitted for approval"}, status=status.HTTP_202_ACCEPTED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.is_superuser:
            return super().update(request, *args, **kwargs)
        else:
            # Create a Pending Entry for "Edit"
            PendingProduct.objects.create(
                submitted_by=request.user,
                pending_type='edit',
                original_product=instance,
                # Copy current fields or updated fields from request...
                # (Simplified for brevity, you map the request.data here)
            )
            return Response({"message": "Edit submitted for approval"}, status=status.HTTP_202_ACCEPTED)


class RentalViewSet(viewsets.ModelViewSet):
    queryset = Rental.objects.all().order_by('-rental_start_date')
    serializer_class = RentalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.user.is_superuser:
            serializer.save(edited_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # Save to PendingRental
            data = serializer.validated_data
            PendingRental.objects.create(
                submitted_by=request.user,
                customer=data['customer'],
                asset=data['asset'],
                rental_start_date=data['rental_start_date'],
                status=data.get('status', 'ongoing'),
                payment_amount=data.get('payment_amount', 0),
            )
            return Response({"message": "Rental submitted for approval"}, status=status.HTTP_202_ACCEPTED)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            # Save to PendingCustomer
            # (Logic similar to above)
            return Response({"message": "Customer submitted for approval"}, status=status.HTTP_202_ACCEPTED)
        return super().create(request, *args, **kwargs)


# ===================================================================
# 4. APPROVAL DASHBOARD (For the Mobile "Admin" Tab)
# ===================================================================

class ApprovalDashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    def list(self, request):
        """Get counts and lists of all pending items"""
        return Response({
            "products": PendingProductSerializer(PendingProduct.objects.all(), many=True).data,
            "rentals": PendingRentalSerializer(PendingRental.objects.all(), many=True).data,
            "customers": PendingCustomerSerializer(PendingCustomer.objects.all(), many=True).data,
            "repairs": PendingRepairSerializer(PendingRepair.objects.all(), many=True).data,
        })

    # --- ACTIONS ---
    
    @action(detail=True, methods=['post'], url_path='approve-product')
    def approve_product(self, request, pk=None):
        pending = get_object_or_404(PendingProduct, pk=pk)
        
        # LOGIC FROM views.py -> approve_product
        if pending.pending_type == 'edit' and pending.original_product:
            prod = pending.original_product
            # Update fields...
            prod.brand = pending.brand
            prod.model_no = pending.model_no
            # ... (Update all fields)
            prod.save()
        else:
            # Create new
            ProductAsset.objects.create(
                type_of_asset=pending.type_of_asset,
                brand=pending.brand,
                model_no=pending.model_no,
                asset_id=pending.asset_id,
                condition_status=pending.condition_status,
                edited_by=pending.submitted_by
                # ... (Add all fields)
            )
            
        pending.delete()
        return Response({"status": "Approved"})

    @action(detail=True, methods=['post'], url_path='reject-product')
    def reject_product(self, request, pk=None):
        get_object_or_404(PendingProduct, pk=pk).delete()
        return Response({"status": "Rejected"})
    
    # (Repeat @action pattern for approve-rental, approve-customer, etc.)