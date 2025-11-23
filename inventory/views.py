from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, ListView, CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db.models import Sum, F
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from .models import Stock, Purchase, Sale
from .forms import StockForm
from transactions.models import SaleBill, PurchaseBill
from datetime import datetime        # for datetime functions
from .filters import StockFilter     # import StockFilter from your app's filters.py
from django_filters.views import FilterView
# ======================
# Add Stock View
# ======================
# inventory/views.py

from django.shortcuts import render, redirect
from .models import Stock
from .forms import StockForm

def add_stock(request):
    if request.method == 'POST':
        form = StockForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory_list')  # or your inventory list URL
    else:
        form = StockForm()
    return render(request, 'inventory/add_stock.html', {'form': form})

class StockListView(FilterView):
    filterset_class = StockFilter
    queryset = Stock.objects.filter(is_deleted=False)
    template_name = 'inventory.html'
    paginate_by = 10


class StockCreateView(SuccessMessageMixin, CreateView):                                 # createview class to add new stock, mixin used to display message
    model = Stock                                                                       # setting 'Stock' model as model
    form_class = StockForm                                                              # setting 'StockForm' form as form
    template_name = "edit_stock.html"                                                   # 'edit_stock.html' used as the template
    success_url = '/inventory'                                                          # redirects to 'inventory' page in the url after submitting the form
    success_message = "Stock has been created successfully"                             # displays message when form is submitted

    def get_context_data(self, **kwargs):                                               # used to send additional context
        context = super().get_context_data(**kwargs)
        context["title"] = 'New Stock'
        context["savebtn"] = 'Add to Inventory'
        return context       


class StockUpdateView(SuccessMessageMixin, UpdateView):                                 # updateview class to edit stock, mixin used to display message
    model = Stock                                                                       # setting 'Stock' model as model
    form_class = StockForm                                                              # setting 'StockForm' form as form
    template_name = "edit_stock.html"                                                   # 'edit_stock.html' used as the template
    success_url = '/inventory'                                                          # redirects to 'inventory' page in the url after submitting the form
    success_message = "Stock has been updated successfully"                             # displays message when form is submitted

    def get_context_data(self, **kwargs):                                               # used to send additional context
        context = super().get_context_data(**kwargs)
        context["title"] = 'Edit Stock'
        context["savebtn"] = 'Update Stock'
        context["delbtn"] = 'Delete Stock'
        return context


class StockDeleteView(View):                                                            # view class to delete stock
    template_name = "delete_stock.html"                                                 # 'delete_stock.html' used as the template
    success_message = "Stock has been deleted successfully"                             # displays message when form is submitted
    
    def get(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        return render(request, self.template_name, {'object' : stock})

    def post(self, request, pk):  
        stock = get_object_or_404(Stock, pk=pk)
        stock.is_deleted = True
        stock.save()                                               
        messages.success(request, self.success_message)
        return redirect('inventory')

# ======================
# Inventory Dashboard
# ======================
def inventory_dashboard(request):
    total_items = Stock.objects.filter(is_deleted=False).count()
    total_qty = Stock.objects.filter(is_deleted=False).aggregate(total=Sum('quantity'))['total'] or 0
    recent_sales = SaleBill.objects.order_by('-time')[:5]
    recent_purchases = PurchaseBill.objects.order_by('-time')[:5]

    context = {
        'total_items': total_items,
        'total_qty': total_qty,
        'recent_sales': recent_sales,
        'recent_purchases': recent_purchases,
    }
    return render(request, "dashboard.html", context)


# ======================
# Stock List Views
# ======================
class StockListView(ListView):
    model = Stock
    template_name = 'stock_list.html'
    context_object_name = 'stocks'

    def get_queryset(self):
        return Stock.objects.filter(is_deleted=False).order_by('name')
    
class StockListView(FilterView):
    filterset_class = StockFilter
    queryset = Stock.objects.filter(is_deleted=False)
    template_name = 'inventory.html'
    paginate_by = 10

class StockCreateView(SuccessMessageMixin, CreateView):
    model = Stock
    form_class = StockForm
    template_name = 'add_stock.html'
    success_url = '/inventory/'
    success_message = "New stock has been added successfully"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"title": "Add New Stock", "savebtn": "Add Stock"})
        return context


class StockUpdateView(SuccessMessageMixin, UpdateView):
    model = Stock
    form_class = StockForm
    template_name = 'inventory/edit_stock.html'
    success_url = '/inventory/'
    success_message = "Stock has been updated successfully"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"title": "Edit Stock", "savebtn": "Update Stock", "delbtn": "Delete Stock"})
        return context


class StockDeleteView(View):
    template_name = 'inventory/delete_stock.html'
    success_message = "Stock has been deleted successfully"

    def get(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        return render(request, self.template_name, {'object': stock})

    def post(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        stock.is_deleted = True
        stock.save()
        messages.success(request, self.success_message)
        return redirect('inventory')


# ======================
# Inventory Balance
# ======================
def inventory_balance(request):
    stocks = Stock.objects.filter(is_deleted=False).order_by('name')
    stock_data = []
    total_quantity = total_purchased = total_sold = total_remaining = 0

    for stock in stocks:
        purchased_total = Purchase.objects.filter(stock=stock).aggregate(total=Sum('quantity'))['total'] or 0
        sold_total = Sale.objects.filter(stock=stock).aggregate(total=Sum('quantity'))['total'] or 0
        remaining = purchased_total - sold_total

        stock_data.append({
            'name': stock.name,
            'quantity_available': stock.quantity,
            'purchased': purchased_total,
            'sold': sold_total,
            'remaining_balance': remaining,
        })

        total_quantity += stock.quantity
        total_purchased += purchased_total
        total_sold += sold_total
        total_remaining += remaining

    context = {
        'stock_data': stock_data,
        'total_quantity': total_quantity,
        'total_purchased': total_purchased,
        'total_sold': total_sold,
        'total_remaining': total_remaining,
    }
    return render(request, 'inventory_balance.html', context)


# ======================
# Inventory Report
# ======================


def inventory_report(request):
    # Get date range from the GET parameters
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        start_date = datetime(2000, 1, 1).date()
        end_date = datetime.today().date()

    stocks = Stock.objects.filter(is_deleted=False).order_by('name')
    stock_data = []
    total_qty = 0
    total_cost = 0

    for stock in stocks:
        # Calculate beginning balance (before start date)
        begin_purchased = Purchase.objects.filter(
            stock=stock, purchased_date__lt=start_date
        ).aggregate(
            qty=Sum('quantity'),
            cost=Sum(F('quantity') * F('unit_cost'))
        )
        begin_sold = Sale.objects.filter(
            stock=stock, sold_date__lt=start_date
        ).aggregate(
            qty=Sum('quantity'),
            cost=Sum(F('quantity') * F('unit_price'))
        )

        begin_qty = (begin_purchased['qty'] or 0) - (begin_sold['qty'] or 0)
        begin_cost = (begin_purchased['cost'] or 0) - (begin_sold['cost'] or 0)

        # Purchases during the period
        purchased = Purchase.objects.filter(
            stock=stock, purchased_date__range=(start_date, end_date)
        ).aggregate(
            qty=Sum('quantity'),
            cost=Sum(F('quantity') * F('unit_cost'))
        )

        # Sales during the period
        sold = Sale.objects.filter(
            stock=stock, sold_date__range=(start_date, end_date)
        ).aggregate(
            qty=Sum('quantity'),
            cost=Sum(F('quantity') * F('unit_price'))
        )

        purchased_qty = purchased['qty'] or 0
        purchased_cost = purchased['cost'] or 0
        sold_qty = sold['qty'] or 0
        sold_cost = sold['cost'] or 0

        # Ending balances
        end_qty = begin_qty + purchased_qty - sold_qty
        end_cost = begin_cost + purchased_cost - sold_cost
        avg_cost = round(end_cost / end_qty, 2) if end_qty > 0 else 0

        stock_data.append({
            'name': stock.name,
            'begin_qty': begin_qty,
            'begin_cost': begin_cost,
            'purchased_qty': purchased_qty,
            'purchased_cost': purchased_cost,
            'sold_qty': sold_qty,
            'sold_cost': sold_cost,
            'end_qty': end_qty,
            'end_cost': end_cost,
            'avg_cost': avg_cost,
        })

        total_qty += end_qty
        total_cost += end_cost

    context = {
        'stocks': stock_data,
        'total_stocks': stocks.count(),
        'total_quantity': total_qty,
        'total_ending_cost': total_cost,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'period_start': start_date,
        'period_end': end_date,
    }
    return render(request, 'inventory_report.html', context)


