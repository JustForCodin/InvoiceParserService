from flask import Blueprint
from controllers.analytics_controller import AnalyticsController
from controllers.dashboard_controller import DashboardController
from controllers.invoice_uploader_controller import InvoiceUploaderController
from controllers.main_page_controller import MainPageController
from controllers.signup_controller import SignupController

blueprint = Blueprint('blueprint', __name__)
blueprint.route('/analytics', methods=['GET', 'POST'])(AnalyticsController().analytics)
blueprint.route('/register', methods=['GET', 'POST'])(SignupController().register)
blueprint.route('/login', methods=['GET', 'POST'])(SignupController().login)
blueprint.route('/logout', methods=['GET', 'POST'])(SignupController().logout)
blueprint.route('/dashboard', methods=['GET', 'POST'])(DashboardController().dashboard)
blueprint.route('/items/<int:invoice_id>', methods=['GET', 'POST'])(DashboardController().show_items)
blueprint.route('/add-invoice', methods=['GET', 'POST'])(InvoiceUploaderController().add_invoice)
blueprint.route('/upload', methods=['GET', 'POST'])(InvoiceUploaderController().upload_file)
blueprint.route('/', methods=['GET', 'POST'])(MainPageController().index)
