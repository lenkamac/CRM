from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncDate
from django.views.decorators.cache import never_cache
from lead.models import Lead
from client.models import Client, Purchase
from product.models import Product
from datetime import timedelta
from django.utils import timezone
import json


app_name = 'dashboard'


# Create your views here.
@login_required
@never_cache
def dashboard(request):
    lead_count = Lead.objects.filter(created_by=request.user, converted_to_client=False).count()
    client_count = Client.objects.filter(created_by=request.user).count()
    latest_leads = Lead.objects.filter(created_by=request.user, converted_to_client=False).order_by('-created_at')[:15]
    latest_clients = Client.objects.filter(created_by=request.user).order_by('-created_at')[:15]

    # Get time period filter from request
    time_period = request.GET.get('period', 'all')

    # Get data type filter (what to display on the graph)
    data_filter = request.GET.get('data_filter', 'all')

    # Get purchase filters
    purchase_product_filter = request.GET.get('purchase_product', 'all')
    purchase_period = request.GET.get('purchase_period', '30days')

    # Calculate date range based on selected period
    today = timezone.now()
    if time_period == '7days':
        start_date = today - timedelta(days=7)
    elif time_period == '30days':
        start_date = today - timedelta(days=30)
    elif time_period == '90days':
        start_date = today - timedelta(days=90)
    elif time_period == '6months':
        start_date = today - timedelta(days=180)
    elif time_period == '1year':
        start_date = today - timedelta(days=365)
    else:  # 'all'
        start_date = None

    # Generate leads over time data for the graph
    leads_query = Lead.objects.filter(created_by=request.user, converted_to_client=False)

    # Apply date filter if not 'all'
    if start_date:
        leads_query = leads_query.filter(created_at__gte=start_date)

    leads_over_time = (
        leads_query
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Generate WON leads over time
    won_leads_query = Lead.objects.filter(created_by=request.user, status=Lead.WON, converted_to_client=False)
    if start_date:
        won_leads_query = won_leads_query.filter(created_at__gte=start_date)

    won_leads_over_time = (
        won_leads_query
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Generate LOST leads over time
    lost_leads_query = Lead.objects.filter(created_by=request.user, status=Lead.LOST, converted_to_client=False)
    if start_date:
        lost_leads_query = lost_leads_query.filter(created_at__gte=start_date)

    lost_leads_over_time = (
        lost_leads_query
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Generate CONTACTED leads over time
    contacted_leads_query = Lead.objects.filter(created_by=request.user, status=Lead.CONTACTED, converted_to_client=False)
    if start_date:
        contacted_leads_query = contacted_leads_query.filter(created_at__gte=start_date)

    contacted_leads_over_time = (
        contacted_leads_query
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Generate clients over time data
    clients_query = Client.objects.filter(created_by=request.user)
    if start_date:
        clients_query = clients_query.filter(created_at__gte=start_date)

    clients_over_time = (
        clients_query
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Prepare data for Chart.js
    lead_dates = [item['date'].strftime('%Y-%m-%d') for item in leads_over_time]
    lead_counts = [item['count'] for item in leads_over_time]

    # Prepare data for Chart.js - Won Leads
    won_lead_dates = [item['date'].strftime('%Y-%m-%d') for item in won_leads_over_time]
    won_lead_counts = [item['count'] for item in won_leads_over_time]

    # Prepare data for Chart.js - Lost Leads
    lost_lead_dates = [item['date'].strftime('%Y-%m-%d') for item in lost_leads_over_time]
    lost_lead_counts = [item['count'] for item in lost_leads_over_time]

    # Prepare data for Chart.js - Contacted Leads
    contacted_lead_dates = [item['date'].strftime('%Y-%m-%d') for item in contacted_leads_over_time]
    contacted_lead_counts = [item['count'] for item in contacted_leads_over_time]

    # Prepare data for Chart.js - Clients
    client_dates = [item['date'].strftime('%Y-%m-%d') for item in clients_over_time]
    client_counts = [item['count'] for item in clients_over_time]

    # Combine all unique dates
    all_dates = sorted(list(set(
        lead_dates + won_lead_dates + lost_lead_dates +
        contacted_lead_dates + client_dates
    )))

    # Create dictionaries for easy lookup
    lead_dict = dict(zip(lead_dates, lead_counts))
    won_lead_dict = dict(zip(won_lead_dates, won_lead_counts))
    lost_lead_dict = dict(zip(lost_lead_dates, lost_lead_counts))
    contacted_lead_dict = dict(zip(contacted_lead_dates, contacted_lead_counts))
    client_dict = dict(zip(client_dates, client_counts))

    # Fill in missing dates with 0
    lead_counts_filled = [lead_dict.get(date, 0) for date in all_dates]
    won_lead_counts_filled = [won_lead_dict.get(date, 0) for date in all_dates]
    lost_lead_counts_filled = [lost_lead_dict.get(date, 0) for date in all_dates]
    contacted_lead_counts_filled = [contacted_lead_dict.get(date, 0) for date in all_dates]
    client_counts_filled = [client_dict.get(date, 0) for date in all_dates]

    # Count leads by status
    won_lead_count = Lead.objects.filter(created_by=request.user, status=Lead.WON, converted_to_client=False).count()
    lost_lead_count = Lead.objects.filter(created_by=request.user, status=Lead.LOST, converted_to_client=False).count()
    contacted_lead_count = Lead.objects.filter(created_by=request.user, status=Lead.CONTACTED, converted_to_client=False).count()

    # ===== PURCHASE DATA FOR GRAPH =====
    # Calculate purchase date range
    purchase_start_date = None
    if purchase_period == '7days':
        purchase_start_date = today - timedelta(days=7)
    elif purchase_period == '30days':
        purchase_start_date = today - timedelta(days=30)
    elif purchase_period == '90days':
        purchase_start_date = today - timedelta(days=90)
    elif purchase_period == '6months':
        purchase_start_date = today - timedelta(days=180)
    elif purchase_period == '1year':
        purchase_start_date = today - timedelta(days=365)

    # Base purchase queryset
    purchases_query = Purchase.objects.filter(created_by=request.user)

    # Apply date filter
    if purchase_start_date:
        purchases_query = purchases_query.filter(created_at__gte=purchase_start_date)

    # Apply product filter
    if purchase_product_filter != 'all':
        purchases_query = purchases_query.filter(product_id=purchase_product_filter)

    # Get purchase data grouped by date, product, and currency
    purchase_data = (
        purchases_query
        .annotate(date=TruncDate('created_at'))
        .values('date', 'product__name', 'product_id', 'currency')
        .annotate(
            total_quantity=Sum('quantity'),
            total_amount=Sum(F('quantity') * F('product__net_price'))
        )
        .order_by('date', 'product__name')
    )

    # Organize data by product and currency
    purchase_products_eur = {}
    purchase_products_usd = {}
    purchase_dates_set = set()

    for item in purchase_data:
        date_str = item['date'].strftime('%Y-%m-%d')
        product_name = item['product__name']
        currency = item['currency']
        purchase_dates_set.add(date_str)

        # Separate by currency
        if currency == 'EUR':
            if product_name not in purchase_products_eur:
                purchase_products_eur[product_name] = {'dates': [], 'quantities': [], 'amounts': []}

            purchase_products_eur[product_name]['dates'].append(date_str)
            purchase_products_eur[product_name]['quantities'].append(item['total_quantity'])
            purchase_products_eur[product_name]['amounts'].append(float(item['total_amount']))
        else:  # USD
            if product_name not in purchase_products_usd:
                purchase_products_usd[product_name] = {'dates': [], 'quantities': [], 'amounts': []}

            # For USD, we need to convert the amount
            purchase_products_usd[product_name]['dates'].append(date_str)
            purchase_products_usd[product_name]['quantities'].append(item['total_quantity'])
            # Get actual USD amount with conversion
            usd_amount = 0
            for purchase in purchases_query.filter(
                created_at__date=item['date'],
                product_id=item['product_id'],
                currency='USD'
            ):
                usd_amount += float(purchase.total)
            purchase_products_usd[product_name]['amounts'].append(usd_amount)

    # Get all products for filter dropdown
    all_products = Product.objects.all().order_by('name')

    # Calculate summary statistics by currency
    from decimal import Decimal
    from core.currency_service import CurrencyConverter

    # EUR revenue (base currency)
    eur_purchases = purchases_query.filter(currency='EUR')
    eur_revenue = eur_purchases.aggregate(
        total=Sum(F('quantity') * F('product__net_price'))
    )['total'] or Decimal('0')
    eur_items = eur_purchases.aggregate(Sum('quantity'))['quantity__sum'] or 0

    # USD revenue (converted purchases)
    usd_purchases = purchases_query.filter(currency='USD')
    usd_revenue = Decimal('0')
    for purchase in usd_purchases:
        usd_revenue += purchase.total
    usd_items = usd_purchases.aggregate(Sum('quantity'))['quantity__sum'] or 0

    # Calculate total revenue in EUR (EUR sales + USD sales converted to EUR)
    usd_revenue_in_eur = CurrencyConverter.convert(usd_revenue, 'USD', 'EUR')
    total_revenue_eur = eur_revenue + usd_revenue_in_eur

    context = {
        'lead_count': lead_count,
        'client_count': client_count,
        'latest_leads': latest_leads,
        'won_lead_count': won_lead_count,
        'lost_lead_count': lost_lead_count,
        'contacted_lead_count': contacted_lead_count,
        'latest_clients': latest_clients,
        'chart_dates': json.dumps(all_dates),
        'lead_counts': json.dumps(lead_counts_filled),
        'client_counts': json.dumps(client_counts_filled),
        'won_lead_counts': json.dumps(won_lead_counts_filled),
        'lost_lead_counts': json.dumps(lost_lead_counts_filled),
        'contacted_lead_counts': json.dumps(contacted_lead_counts_filled),
        'selected_period': time_period,
        # Purchase data
        'purchase_chart_data': json.dumps({
            'dates': sorted(list(purchase_dates_set)),
            'products_eur': purchase_products_eur,
            'products_usd': purchase_products_usd
        }),
        'all_products': all_products,
        'selected_purchase_product': purchase_product_filter,
        'selected_purchase_period': purchase_period,
        'total_revenue_eur': float(eur_revenue),
        'total_revenue_usd': float(usd_revenue),
        'total_revenue_all_in_eur': float(total_revenue_eur),
        'total_items_eur': eur_items,
        'total_items_usd': usd_items,
        'total_items': eur_items + usd_items,
    }

    return render(request, 'dashboard/dashboard.html', context)