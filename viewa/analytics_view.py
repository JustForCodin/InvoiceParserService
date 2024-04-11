from flask import render_template


class AnalyticsView:
    def render(self, template: str, invoices_per_sender: str, purchased_products: str, product_costs: str, customer):
        return render_template(template, invoices_per_sender=invoices_per_sender,
                                purchased_products=purchased_products,
                                product_costs=product_costs, customer=customer)