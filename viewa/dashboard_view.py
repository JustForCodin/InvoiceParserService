from flask import render_template


class DashboardView:
    def render(self, template: str, customer, invoices):
        return render_template(template, customer=customer, invoices=invoices)