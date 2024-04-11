from flask import render_template


class MainPageView:
    def render(self, template: str):
        return render_template(template)