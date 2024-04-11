from flask import *
from db.models import Customer, Invoice, InvoiceItem
from viewa.dashboard_view import DashboardView


class DashboardController:
    def dashboard(self):
        if 'customer_id' in session:
            customer_id = session['customer_id']
            customer = Customer.query.get(customer_id)
            invoices = customer.invoices
            return DashboardView().render('dashboard.html', customer, invoices)
        return redirect(url_for('blueprint.login'))


    def show_items(self, invoice_id):
        invoice = Invoice.query.get_or_404(invoice_id)
        items = InvoiceItem.query.filter_by(InvoiceID=invoice_id).all()
        return render_template('items.html', invoice=invoice, items=items)