from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import View, ListView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse_lazy


from .models import (
    Supplier, PurchaseBill, PurchaseItem, PurchaseBillDetails,
    SaleBill, SaleItem, SaleBillDetails
)
from inventory.models import Stock
from .forms import (
    SupplierForm, SelectSupplierForm,
    PurchaseItemFormset, PurchaseDetailsForm,
    SaleForm, SaleItemFormset, SaleDetailsForm
)

# ---------- SUPPLIER VIEWS ----------

# List all suppliers
class SupplierListView(ListView):
    model = Supplier
    template_name = "suppliers/suppliers_list.html"
    queryset = Supplier.objects.filter(is_deleted=False)
    paginate_by = 10
# ---------- SUPPLIER SELECTION ----------
class SelectSupplierView(View):
    form_class = SelectSupplierForm
    template_name = 'purchases/select_supplier.html'

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            supplier = form.cleaned_data['supplier']  # Supplier object
            return redirect('new-purchase', pk=supplier.pk)  # pass PK, not object

        return render(request, self.template_name, {'form': form})
    
    # forms.py
from django import forms
from .models import Supplier
class SelectSupplierView(View):
    template_name = 'purchases/select_supplier.html'
    form_class = SelectSupplierForm

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            supplier = form.cleaned_data['supplier']  # This is a Supplier object
            return redirect('new-purchase', pk=supplier.pk)  # Use the PK, not the object
        return render(request, self.template_name, {'form': form})

# View supplier details and purchase bills
class SupplierView(View):
    def get(self, request, name):
        supplier = get_object_or_404(Supplier, name=name)
        bills = PurchaseBill.objects.filter(supplier=supplier)
        paginator = Paginator(bills, 10)
        page = request.GET.get('page', 1)
        try:
            paginated = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            paginated = paginator.page(1)

        return render(request, 'suppliers/supplier.html', {
            'supplier': supplier,
            'bills': paginated
        })


# Create new supplier
class SupplierCreateView(SuccessMessageMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    success_url = '/transactions/suppliers'
    success_message = "Supplier created successfully"
    template_name = "suppliers/edit_supplier.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'New Supplier'
        context["savebtn"] = 'Add Supplier'
        return context


# Update existing supplier
class SupplierUpdateView(SuccessMessageMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    success_url = '/transactions/suppliers'
    success_message = "Supplier updated successfully"
    template_name = "suppliers/edit_supplier.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Edit Supplier'
        context["savebtn"] = 'Save Changes'
        context["delbtn"] = 'Delete Supplier'
        return context


# Soft delete a supplier
class SupplierDeleteView(View):
    template_name = "suppliers/delete_supplier.html"
    success_message = "Supplier deleted successfully"

    def get(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        return render(request, self.template_name, {'object': supplier})

    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        supplier.is_deleted = True
        supplier.save()
        messages.success(request, self.success_message)
        return redirect('suppliers-list')


# Select a supplier before creating a purchase
class SelectSupplierView(View):
    form_class = SelectSupplierForm
    template_name = 'purchases/select_supplier.html'

    def get(self, request):
        return render(request, self.template_name, {'form': self.form_class()})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            supplier = form.cleaned_data['supplier']  # This is a Supplier object
            # Redirect using supplier.pk to avoid TypeError
            return redirect('new-purchase', pk=supplier.pk)
        return render(request, self.template_name, {'form': form})
    

# ---------- PURCHASE VIEWS ----------


# List of all purchase bills
class PurchaseView(ListView):
    model = PurchaseBill
    template_name = "purchases/purchases_list.html"
    context_object_name = 'bills'
    ordering = ['-time']
    paginate_by = 10


# Create a new purchase bill for a selected supplier
class PurchaseCreateView(View):
    template_name = 'purchases/new-purchase.html'

    def get(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        formset = PurchaseItemFormset()
        return render(request, self.template_name, {
            'formset': formset,
            'supplier': supplier
        })

    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        formset = PurchaseItemFormset(request.POST)

        if formset.is_valid():
            # Create the purchase bill
            bill = PurchaseBill.objects.create(supplier=supplier)
            PurchaseBillDetails.objects.create(billno=bill)

            # Process each item in the formset
            for form in formset:
                item = form.save(commit=False)
                item.billno = bill
                item.totalprice = item.perprice * item.quantity

                # Update stock quantity
                stock = get_object_or_404(Stock, name=item.stock.name)
                stock.quantity += item.quantity
                stock.save()

                item.save()

            messages.success(request, "Purchased items registered successfully.")
            return redirect('purchase-bill', billno=bill.billno)

        return render(request, self.template_name, {
            'formset': formset,
            'supplier': supplier
        })


# Delete a purchase bill
class PurchaseDeleteView(SuccessMessageMixin, DeleteView):
    model = PurchaseBill
    template_name = "delete_purchase.html"
    success_url = '/transactions/purchases'

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        # Roll back stock quantities
        for item in PurchaseItem.objects.filter(billno=self.object.billno):
            stock = get_object_or_404(Stock, name=item.stock.name)
            if not stock.is_deleted:
                stock.quantity -= item.quantity
                stock.save()
        messages.success(self.request, "Purchase bill deleted successfully.")
        return super().delete(*args, **kwargs)


# Display a purchase bill
class PurchaseBillView(View):
    template_name = "bill/purchase_bill.html"
    bill_base = "bill/bill_base.html"

    def get(self, request, billno):
        bill = get_object_or_404(PurchaseBill, billno=billno)
        items = PurchaseItem.objects.filter(billno=billno)
        details = get_object_or_404(PurchaseBillDetails, billno=billno)

        return render(request, self.template_name, {
            'bill': bill,
            'items': items,
            'billdetails': details,
            'bill_base': self.bill_base,
        })

    def post(self, request, billno):
        form = PurchaseDetailsForm(request.POST)
        if form.is_valid():
            details = get_object_or_404(PurchaseBillDetails, billno=billno)
            for field, value in form.cleaned_data.items():
                setattr(details, field, value)
            details.save()
            messages.success(request, "Purchase bill updated.")
        return self.get(request, billno)


# ---------- SALE VIEWS ----------
class SaleView(ListView):
    model = SaleBill
    template_name = "sales/sales_list.html"
    context_object_name = 'bills'
    ordering = ['-time']
    paginate_by = 10


class SaleCreateView(View):
    template_name = 'sales/new_sale.html'

    def get(self, request):
        return render(request, self.template_name, {
            'form': SaleForm(),
            'formset': SaleItemFormset(),
            'stocks': Stock.objects.filter(is_deleted=False)
        })

    def post(self, request):
        form = SaleForm(request.POST)
        formset = SaleItemFormset(request.POST)
        if form.is_valid() and formset.is_valid():
            bill = form.save()
            SaleBillDetails.objects.create(billno=bill)

            for form in formset:
                item = form.save(commit=False)
                item.billno = bill
                item.totalprice = item.perprice * item.quantity
                stock = get_object_or_404(Stock, name=item.stock.name)
                stock.quantity -= item.quantity
                stock.save()
                item.save()

            messages.success(request, "Sale registered successfully.")
            return redirect('sale-bill', billno=bill.billno)

        return render(request, self.template_name, {
            'form': form,
            'formset': formset,
        })


class SaleDeleteView(SuccessMessageMixin, DeleteView):
    model = SaleBill
    template_name = "sales/delete_sale.html"
    success_url = '/transactions/sales'

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        for item in SaleItem.objects.filter(billno=self.object.billno):
            stock = get_object_or_404(Stock, name=item.stock.name)
            if not stock.is_deleted:
                stock.quantity += item.quantity
                stock.save()
        messages.success(self.request, "Sale bill deleted successfully.")
        return super().delete(*args, **kwargs)


class SaleBillView(View):
    template_name = "bill/sale_bill.html"
    bill_base = "bill/bill_base.html"

    def get(self, request, billno):
        bill = get_object_or_404(SaleBill, billno=billno)
        items = SaleItem.objects.filter(billno=billno)
        details = get_object_or_404(SaleBillDetails, billno=billno)

        # --- Calculate totals ---
        subtotal = sum(item.totalprice for item in items)
        vat = subtotal * 0.15
        total_after_vat = subtotal + vat
        withhold = total_after_vat * 0.03
        net_payable = total_after_vat - withhold

        # Convert net amount to words
        net_in_words = num2words(net_payable, lang='en').title()

        context = {
            'bill': bill,
            'items': items,
            'billdetails': details,
            'bill_base': self.bill_base,
            'subtotal': subtotal,
            'vat': vat,
            'total_after_vat': total_after_vat,
            'withhold': withhold,
            'net_payable': net_payable,
            'net_in_words': net_in_words,
        }

        return render(request, self.template_name, context)

    def post(self, request, billno):
        form = SaleDetailsForm(request.POST)
        if form.is_valid():
            details = get_object_or_404(SaleBillDetails, billno=billno)
            for field in form.cleaned_data:
                setattr(details, field, form.cleaned_data[field])
            details.save()
            messages.success(request, "Sale bill updated.")
        return self.get(request, billno)

class SelectSupplierView(View):
    template_name = 'purchases/select_supplier.html'
    form_class = SelectSupplierForm

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            supplier = form.cleaned_data['supplier']  # This is a Supplier instance
            # Redirect using supplier.pk
            return redirect('new-purchase', pk=supplier.pk)
        return render(request, self.template_name, {'form': form})