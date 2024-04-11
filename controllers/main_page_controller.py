from flask import *
from viewa.main_page_view import MainPageView


class MainPageController:
    def index(self):
        return MainPageView().render('index.html')