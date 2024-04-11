from flask import render_template


class SignupView:
    def render(self, tempate: str):
        return render_template(tempate)