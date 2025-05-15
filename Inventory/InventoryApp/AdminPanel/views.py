from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Sum, F, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone


from inventory.forms import PhoneForm
from inventory.models import Product, Phone, Inventory, Brand, Category

from Inventory.InventoryApp.inventory.models import Accessory


@login_required
@permission_required('accounts.can_access_admin_portal', raise_exception=True)
def dashboard(request):
    """Admin dashboard view with summary statistics"""
    from Sales.models import Sale
    # Get current date
    today = timezone.now().date()

    # Get sales statistics
    today_sales = Sale.objects.filter(sale_date__date=today)
    today_sales_count = today_sales.count()
    today_sales_amount = today_sales.aggregate(total=Sum('total_amount'))['total'] or 0

    # Get inventory statistics
    low_stock_items = Inventory.objects.filter(quantity__lte=F('reorder_level')).count()
    total_products = Product.objects.filter(is_active=True).count()

    # Get user's branch if assigned
    if request.CustomUser.branch:
        branch = request.CustomUser.branch
        branch_sales = Sale.objects.filter(branch=branch, sale_date__date=today)
        branch_sales_count = branch_sales.count()
        branch_sales_amount = branch_sales.aggregate(total=Sum('total_amount'))['total'] or 0
    else:
        branch = None
        branch_sales_count = 0
        branch_sales_amount = 0

    context = {
        'today_sales_count': today_sales_count,
        'today_sales_amount': today_sales_amount,
        'low_stock_items': low_stock_items,
        'total_products': total_products,
        'branch': branch,
        'branch_sales_count': branch_sales_count,
        'branch_sales_amount': branch_sales_amount,
    }

    return render(request, 'AdminPanel/dashboard.html', context)


@login_required
@permission_required('inventory.view_phone', raise_exception=True)
def phone_list(request):
    """List view for phones with filter options"""
    # Get filter parameters
    brand = request.GET.get('brand')
    category = request.GET.get('category')
    search = request.GET.get('search')

    # Base queryset
    phones = Phone.objects.all()

    # Apply filters
    if brand:
        phones = phones.filter(brand__id=brand)
    if category:
        phones = phones.filter(category__id=category)
    if search:
        phones = phones.filter(
            Q(name__icontains=search) |
            Q(model_number__icontains=search) |
            Q(sku__icontains=search) |
            Q(barcode__icontains=search)
        )

    # Get filter options for the template
    brands = Brand.objects.all()
    categories = Category.objects.filter(parent__isnull=True) | Category.objects.filter(parent__name__icontains='phone')

    context = {
        'phones': phones,
        'brands': brands,
        'categories': categories,
        'selected_brand': brand,
        'selected_category': category,
        'search': search,
    }

    return render(request, 'AdminPanel/phones.html', context)


@login_required
@permission_required('inventory.add_phone', raise_exception=True)
def phone_add(request):
    """Add new phone view"""
    if request.method == 'POST':
        form = PhoneForm(request.POST, request.FILES)
        if form.is_valid():
            phone = form.save()
            messages.success(request, f'Phone "{phone.name}" has been added successfully.')
            return redirect('AdminPanel:phone_list')
    else:
        form = PhoneForm()

    context = {
        'form': form,
        'title': 'Add New Phone',
    }

    return render(request, 'AdminPanel/phones_form.html', context)


@login_required
@permission_required('inventory.change_phone', raise_exception=True)
def phone_edit(request, pk):
    """Edit existing phone view"""
    phone = get_object_or_404(Phone, pk=pk)

    if request.method == 'POST':
        form = PhoneForm(request.POST, request.FILES, instance=phone)
        if form.is_valid():
            phone = form.save()
            messages.success(request, f'Phone "{phone.name}" has been updated successfully.')
            return redirect('AdminPanel:phone_list')
    else:
        form = PhoneForm(instance=phone)

    context = {
        'form': form,
        'title': f'Edit Phone: {phone.name}',
        'phone': phone,
    }

    return render(request, 'AdminPanel/phones_form.html', context)


@login_required
@permission_required('inventory.delete_phone', raise_exception=True)
def phone_delete(request, pk):
    """Delete phone view"""
    phone = get_object_or_404(Phone, pk=pk)

    if request.method == 'POST':
        phone_name = phone.name
        phone.delete()
        messages.success(request, f'Phone "{phone_name}" has been deleted successfully.')
        return redirect('AdminPanel:phone_list')

    context = {
        'phone': phone,
    }

    return render(request, 'AdminPanel/phones_delete.html', context)


@login_required
@permission_required('inventory.view_accessory', raise_exception=True)
def accessory_list(request):
    brand = request.GET.get('brand')
    category = request.GET.get('category')
    search = request.GET.get('search')

    accessories = Accessory.objects.all()

    if brand:
        accessories = accessories.filter(brand__id=brand)
    if category:
        accessories = accessories.filter(category__id=category)
    if search:
        accessories = accessories.filter(
            Q(name__icontains=search) |
            Q(sku__icontains=search) |
            Q(barcode__icontains=search)
        )

    brands = Brand.objects.all()
    categories = Category.objects.filter(parent__isnull=True) | Category.objects.filter(parent__name__icontains='accessory')

    context = {
        'accessories': accessories,
        'brands': brands,
        'categories': categories,
        'selected_brand': brand,
        'selected_category': category,
        'search': search,
    }

    return render(request, 'AdminPanel/Accessories.html', context)


@login_required
@permission_required('inventory.add_accessory', raise_exception=True)
def accessory_add(request):
    from inventory.forms import AccessoryForm

    if request.method == 'POST':
        form = AccessoryForm(request.POST, request.FILES)
        if form.is_valid():
            accessory = form.save()
            messages.success(request, f'Accessory "{accessory.name}" has been added successfully.')
            return redirect('admin_portal:accessory_list')
    else:
        form = AccessoryForm()

    context = {
        'form': form,
        'title': 'Add New Accessory',
    }

    return render(request, 'admin_portal/accessories/form.html', context)


@login_required
@permission_required('inventory.change_accessory', raise_exception=True)
def accessory_edit(request, pk):
    from inventory.forms import AccessoryForm
    accessory = get_object_or_404(Accessory, pk=pk)

    if request.method == 'POST':
        form = AccessoryForm(request.POST, request.FILES, instance=accessory)
        if form.is_valid():
            accessory = form.save()
            messages.success(request, f'Accessory "{accessory.name}" has been updated successfully.')
            return redirect('admin_portal:accessory_list')
    else:
        form = AccessoryForm(instance=accessory)

    context = {
        'form': form,
        'title': f'Edit Accessory: {accessory.name}',
        'accessory': accessory,
    }

    return render(request, 'admin_portal/accessories/form.html', context)


@login_required
@permission_required('inventory.delete_accessory', raise_exception=True)
def accessory_delete(request, pk):
    accessory = get_object_or_404(Accessory, pk=pk)

    if request.method == 'POST':
        accessory_name = accessory.name
        accessory.delete()
        messages.success(request, f'Accessory "{accessory_name}" has been deleted successfully.')
        return redirect('admin_portal:accessory_list')

    context = {
        'accessory': accessory,
    }

    return render(request, 'admin_portal/accessories/delete.html', context)
