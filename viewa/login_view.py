from flask import render_template


class LoginView:
    def render(self, template: str):
        return render_template(template)