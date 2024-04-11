from flask import render_template


class InvoiceUploaderView:
    def render(self, template: str):
        return render_template(template)