from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from django.apps import apps

from inventory.models import Product, Phone, Accessory, Inventory
from Sales.models import Sale, SaleItem, Customer
from Sales.forms import SaleForm, SaleItemForm, CustomerForm



@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def dashboard(request):
    """Staff dashboard view with summary statistics"""
    # Get current date
    today = timezone.now().date()

    # Get user's branch
    branch = request.user.branch

    if not branch:
        messages.warning(request, "You are not assigned to any branch. Please contact your administrator.")
        return redirect('accounts:profile')

    # Get sales statistics for this branch and this staff
    today_sales = Sale.objects.filter(branch=branch, sale_date__date=today)
    my_sales = today_sales.filter(staff=request.user)

    today_sales_count = today_sales.count()
    today_sales_amount = today_sales.aggregate(total=Sum('total_amount'))['total'] or 0

    my_sales_count = my_sales.count()
    my_sales_amount = my_sales.aggregate(total=Sum('total_amount'))['total'] or 0

    # Get inventory statistics for this branch
    low_stock_items = Inventory.objects.filter(branch=branch, quantity__lte=F('reorder_level')).count()
    out_of_stock_items = Inventory.objects.filter(branch=branch, quantity=0).count()

    context = {
        'today_sales_count': today_sales_count,
        'today_sales_amount': today_sales_amount,
        'my_sales_count': my_sales_count,
        'my_sales_amount': my_sales_amount,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
        'branch': branch,
    }

    return render(request, 'staff_portal/dashboard.html', context)


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def pos(request):
    """Point of Sale (POS) view"""
    # Get user's branch
    branch = request.user.branch

    if not branch:
        messages.warning(request, "You are not assigned to any branch. Please contact your administrator.")
        return redirect('staff_portal:dashboard')

    # Get products available in this branch's inventory
    products = Product.objects.filter(
        inventory__branch=branch,
        inventory__quantity__gt=0,
        is_active=True
    ).distinct()

    # Initialize forms
    sale_form = SaleForm(branch=branch)
    item_form = SaleItemForm(branch=branch)
    customer_form = CustomerForm()

    # Get recent customers for quick selection
    recent_customers = Customer.objects.order_by('-created_at')[:10]

    context = {
        'branch': branch,
        'products': products,
        'sale_form': sale_form,
        'item_form': item_form,
        'customer_form': customer_form,
        'recent_customers': recent_customers,
    }

    return render(request, 'staff_portal/pos/index.html', context)


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def create_sale(request):
    """Create new sale API view"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    # Get user's branch
    branch = request.user.branch

    if not branch:
        return JsonResponse({'status': 'error', 'message': 'You are not assigned to any branch'}, status=400)

    # Create empty sale
    sale = Sale.objects.create(
        branch=branch,
        staff=request.user,
        sale_date=timezone.now(),
    )

    return JsonResponse({
        'status': 'success',
        'sale_id': sale.id,
        'invoice_number': sale.invoice_number,
    })


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def add_sale_item(request):
    """Add item to sale API view"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    # Get sale ID from request
    sale_id = request.POST.get('sale_id')
    if not sale_id:
        return JsonResponse({'status': 'error', 'message': 'Sale ID is required'}, status=400)

    # Get the sale
    try:
        sale = Sale.objects.get(id=sale_id)
    except Sale.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Sale not found'}, status=404)

    # Process the form
    form = SaleItemForm(request.POST, branch=sale.branch)
    if form.is_valid():
        # Create sale item but don't save to database yet
        sale_item = form.save(commit=False)
        sale_item.sale = sale

        # Get product price
        product = form.cleaned_data['product']
        price = product.selling_price

        # Calculate item total
        quantity = form.cleaned_data['quantity']
        discount = form.cleaned_data['discount'] or 0
        item_total = (price * quantity) - discount

        # Save the item with calculated values
        sale_item.unit_price = price
        sale_item.total_price = item_total
        sale_item.save()

        # Update inventory
        inventory = Inventory.objects.get(product=product, branch=sale.branch)
        inventory.quantity -= quantity
        inventory.save()

        # Update sale totals
        sale.update_totals()

        return JsonResponse({
            'status': 'success',
            'item_id': sale_item.id,
            'product_name': product.name,
            'quantity': quantity,
            'unit_price': float(price),
            'discount': float(discount),
            'total_price': float(item_total),
            'sale_subtotal': float(sale.subtotal),
            'sale_total': float(sale.total_amount),
        })
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def remove_sale_item(request, item_id):
    """Remove item from sale API view"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    # Get the sale item
    try:
        sale_item = SaleItem.objects.get(id=item_id)
    except SaleItem.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Sale item not found'}, status=404)

    # Get associated sale
    sale = sale_item.sale

    # Return quantity to inventory
    inventory = Inventory.objects.get(product=sale_item.product, branch=sale.branch)
    inventory.quantity += sale_item.quantity
    inventory.save()

    # Delete the item
    sale_item.delete()

    # Update sale totals
    sale.update_totals()

    return JsonResponse({
        'status': 'success',
        'sale_subtotal': float(sale.subtotal),
        'sale_total': float(sale.total_amount),
    })


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def update_sale(request, sale_id):
    """Update sale details API view"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    # Get the sale
    try:
        sale = Sale.objects.get(id=sale_id)
    except Sale.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Sale not found'}, status=404)

    # Process the form
    form = SaleForm(request.POST, instance=sale, branch=sale.branch)
    if form.is_valid():
        # Update customer if provided
        customer_id = request.POST.get('customer')
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
                sale.customer = customer
            except Customer.DoesNotExist:
                pass

        # Update other fields
        sale.payment_method = form.cleaned_data['payment_method']
        sale.discount_amount = form.cleaned_data['discount_amount'] or 0
        sale.notes = form.cleaned_data['notes']

        # Save changes
        sale.save()

        # Update totals
        sale.update_totals()

        return JsonResponse({
            'status': 'success',
            'customer_name': sale.customer.name if sale.customer else 'Walk-in Customer',
            'payment_method': sale.get_payment_method_display(),
            'discount_amount': float(sale.discount_amount),
            'total_amount': float(sale.total_amount),
        })
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def add_customer(request):
    """Add new customer API view"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    # Process the form
    form = CustomerForm(request.POST)
    if form.is_valid():
        customer = form.save()
        return JsonResponse({
            'status': 'success',
            'customer_id': customer.id,
            'customer_name': customer.name,
        })
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def search_products(request):
    """Search products API view"""
    # Get user's branch
    branch = request.user.branch

    if not branch:
        return JsonResponse({'status': 'error', 'message': 'You are not assigned to any branch'}, status=400)

    # Get search term
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'status': 'error', 'message': 'Search query is required'}, status=400)

    # Search for products
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(sku__icontains=query) |
        Q(barcode__icontains=query),
        inventory__branch=branch,
        inventory__quantity__gt=0,
        is_active=True
    ).distinct()

    # Format results
    results = []
    for product in products:
        inventory = product.inventory.get(branch=branch)
        results.append({
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'price': float(product.selling_price),
            'quantity_available': inventory.quantity,
            'product_type': 'Phone' if hasattr(product, 'phone') else 'Accessory',
            'image_url': product.image.url if product.image else None,
        })

    return JsonResponse({
        'status': 'success',
        'results': results,
    })


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def search_customers(request):
    """Search customers API view"""
    # Get search term
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'status': 'error', 'message': 'Search query is required'}, status=400)

    # Search for customers
    customers = Customer.objects.filter(
        Q(name__icontains=query) |
        Q(email__icontains=query) |
        Q(phone_number__icontains=query)
    )

    # Format results
    results = []
    for customer in customers:
        results.append({
            'id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'phone_number': customer.phone_number,
        })

    return JsonResponse({
        'status': 'success',
        'results': results,
    })


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def complete_sale(request, sale_id):
    """Complete sale and print receipt"""
    # Get the sale
    sale = get_object_or_404(Sale, id=sale_id)

    # Update sale status
    sale.is_completed = True
    sale.save()

    # Get sale items
    items = sale.items.all()

    context = {
        'sale': sale,
        'items': items,
    }

    # Check if print receipt is requested
    if request.GET.get('print') == 'true':
        return render(request, 'staff_portal/sales/receipt.html', context)

    # Show sale completed page
    return render(request, 'staff_portal/sales/completed.html', context)


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def cancel_sale(request, sale_id):
    """Cancel sale view"""
    # Get the sale
    sale = get_object_or_404(Sale, id=sale_id)

    if request.method == 'POST':
        # Return items to inventory
        for item in sale.items.all():
            inventory = Inventory.objects.get(product=item.product, branch=sale.branch)
            inventory.quantity += item.quantity
            inventory.save()

        # Delete the sale
        sale.delete()

        messages.success(request, f'Sale #{sale.invoice_number} has been cancelled.')
        return redirect('staff_portal:pos')

    context = {
        'sale': sale,
    }

    return render(request, 'staff_portal/sales/cancel.html', context)


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def sales_history(request):
    """View sales history"""
    # Get user's branch
    branch = request.user.branch

    if not branch:
        messages.warning(request, "You are not assigned to any branch. Please contact your administrator.")
        return redirect('staff_portal:dashboard')

    # Get filter parameters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    payment_method = request.GET.get('payment_method')
    only_mine = request.GET.get('only_mine') == 'true'

    # Base queryset
    sales = Sale.objects.filter(branch=branch, is_completed=True)

    # Apply filters
    if date_from:
        sales = sales.filter(sale_date__date__gte=date_from)
    if date_to:
        sales = sales.filter(sale_date__date__lte=date_to)
    if payment_method:
        sales = sales.filter(payment_method=payment_method)
    if only_mine:
        sales = sales.filter(staff=request.user)

    # Order by most recent
    sales = sales.order_by('-sale_date')

    context = {
        'sales': sales,
        'date_from': date_from,
        'date_to': date_to,
        'payment_method': payment_method,
        'only_mine': only_mine,
    }

    return render(request, 'staff_portal/sales/history.html', context)


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def sale_detail(request, sale_id):
    """View sale details"""
    # Get the sale
    sale = get_object_or_404(Sale, id=sale_id)

    # Get sale items
    items = sale.items.all()

    context = {
        'sale': sale,
        'items': items,
    }

    return render(request, 'staff_portal/sales/detail.html', context)


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def inventory_list(request):
    """View branch inventory"""
    # Get user's branch
    branch = request.user.branch

    if not branch:
        messages.warning(request, "You are not assigned to any branch. Please contact your administrator.")
        return redirect('staff_portal:dashboard')

    # Get filter parameters
    category = request.GET.get('category')
    stock_status = request.GET.get('stock_status')
    search = request.GET.get('search')

    # Base queryset
    inventory_items = Inventory.objects.filter(branch=branch)

    # Apply filters
    if category:
        inventory_items = inventory_items.filter(product__category__id=category)

    if stock_status == 'low':
        inventory_items = inventory_items.filter(quantity__lte=F('reorder_level'), quantity__gt=0)
    elif stock_status == 'out':
        inventory_items = inventory_items.filter(quantity=0)
    elif stock_status == 'available':
        inventory_items = inventory_items.filter(quantity__gt=F('reorder_level'))

    if search:
        inventory_items = inventory_items.filter(
            Q(product__name__icontains=search) |
            Q(product__sku__icontains=search) |
            Q(product__barcode__icontains=search)
        )

    # Get categories for filter
    from inventory.models import Category
    categories = Category.objects.all()

    context = {
        'inventory_items': inventory_items,
        'categories': categories,
        'selected_category': category,
        'stock_status': stock_status,
        'search': search,
        'branch': branch,
    }

    return render(request, 'staff_portal/inventory/list.html', context)


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def product_detail(request, product_id):
    """View product details"""
    # Get the product
    product = get_object_or_404(Product, id=product_id)

    # Get user's branch
    branch = request.user.branch

    if not branch:
        messages.warning(request, "You are not assigned to any branch. Please contact your administrator.")
        return redirect('staff_portal:dashboard')

    # Get inventory for this product in this branch
    try:
        inventory = Inventory.objects.get(product=product, branch=branch)
    except Inventory.DoesNotExist:
        inventory = None

    # Get sales history for this product in this branch
    sales = SaleItem.objects.filter(
        product=product,
        sale__branch=branch,
        sale__is_completed=True
    ).order_by('-sale__sale_date')[:10]

    context = {
        'product': product,
        'inventory': inventory,
        'sales': sales,
        'branch': branch,
    }

    return render(request, 'staff_portal/inventory/detail.html', context)


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def customer_list(request):
    """View customers"""
    # Get filter parameters
    search = request.GET.get('search')

    # Base queryset
    customers = Customer.objects.all()

    # Apply filters
    if search:
        customers = customers.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone_number__icontains=search)
        )

    # Order by recent
    customers = customers.order_by('-created_at')

    context = {
        'customers': customers,
        'search': search,
    }

    return render(request, 'staff_portal/customers/list.html', context)


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def customer_detail(request, customer_id):
    """View customer details"""
    # Get the customer
    customer = get_object_or_404(Customer, id=customer_id)

    # Get user's branch
    branch = request.user.branch

    # Get purchase history for this customer in this branch
    sales = Sale.objects.filter(
        customer=customer,
        branch=branch,
        is_completed=True
    ).order_by('-sale_date')

    context = {
        'customer': customer,
        'sales': sales,
    }

    return render(request, 'staff_portal/customers/detail.html', context)


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def customer_add(request):
    """Add new customer view"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer "{customer.name}" has been added successfully.')
            return redirect('staff_portal:customer_list')
    else:
        form = CustomerForm()

    context = {
        'form': form,
        'title': 'Add New Customer',
    }

    return render(request, 'staff_portal/customers/form.html', context)


@login_required
@permission_required('accounts.can_access_staff_portal', raise_exception=True)
def customer_edit(request, customer_id):
    """Edit customer view"""
    # Get the customer
    customer = get_object_or_404(Customer, id=customer_id)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer "{customer.name}" has been updated successfully.')
            return redirect('staff_portal:customer_detail', customer_id=customer.id)
    else:
        form = CustomerForm(instance=customer)

    context = {
        'form': form,
        'title': f'Edit Customer: {customer.name}',
        'customer': customer,
    }

    return render(request, 'staff_portal/customers/form.html', context)