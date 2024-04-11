from collections import defaultdict
from datetime import datetime
from flask import *
from db.models import Customer, Invoice, InvoiceItem
from viewa.analytics_view import AnalyticsView
from app import _db


class AnalyticsController:
    def analytics(self):
        if 'customer_id' in session:
            customer_id = session['customer_id']
            customer = Customer.query.get(customer_id)
            current_month = datetime.now().month
            current_year = datetime.now().year

            # data for bar diagram representing monthly amount of invoices per sender
            invoices_per_sender = defaultdict(int)
            invoices = Invoice.query.filter(Invoice.CustomerID == customer_id,
                                            _db.extract('month', Invoice.InvoiceDate) <= current_month,
                                            _db.extract('year', Invoice.InvoiceDate) <= current_year).all()
            for invoice in invoices:
                invoices_per_sender[invoice.BillFrom] += 1

            invoices_per_sender = dict(invoices_per_sender)

            # data for bar diagram representing monthly expenses
            # monthly_expenses = defaultdict(float)
            # for invoice in invoices:
            #     items = InvoiceItem.query.filter_by(InvoiceID=invoice.InvoiceID).all()
            #     for item in items:
            #         monthly_expenses[current_month] += float(item.LineTotal)

            # monthly_expenses = dict(monthly_expenses)
            # print(f"monthly_enxpenses ==== {json.dumps(monthly_expenses)}")

            # data for bar diagram representing monthly amount of products
            purchased_products = defaultdict(int)
            for invoice in invoices:
                items = InvoiceItem.query.filter_by(InvoiceID=invoice.InvoiceID).all()
                for item in items:
                    purchased_products[item.ItemDescription] += int(item.Quantity)

            purchased_products = dict(purchased_products)

            # data for bar diagram representing products costs
            product_costs = defaultdict(float)
            for invoice in invoices:
                items = InvoiceItem.query.filter_by(InvoiceID=invoice.InvoiceID).all()
                for item in items:
                    product_costs[item.ItemDescription] += float(item.LineTotal)

            product_costs = dict(product_costs)

            invoices_per_sender_json = json.dumps({k: v for k, v in invoices_per_sender.items()})
            # monthly_expenses_json = json.dumps(monthly_expenses)
            purchased_products_json = json.dumps({k: v for k, v in purchased_products.items()})
            product_costs_json = json.dumps({k: v for k, v in product_costs.items()})

            # return render_template('analytics.html', invoices_per_sender=invoices_per_sender_json,
            #                     purchased_products=purchased_products_json,
            #                     product_costs=product_costs_json, customer=customer)
            return AnalyticsView().render('analytics.html', invoices_per_sender_json, 
                                          purchased_products_json, product_costs_json, customer)

        return redirect(url_for('login'))