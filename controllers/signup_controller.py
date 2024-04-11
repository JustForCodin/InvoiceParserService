from flask import *
from db.models import Customer
from services.hash_gen import generate_password_hash, check_password_hash
from viewa.signup_view import SignupView
from viewa.login_view import LoginView
from app import _db


class SignupController:
    def register(self):

        if request.method == 'POST':
            full_name = request.form['full_name']
            email = request.form['email']
            password = request.form['password']

            hashed_password = generate_password_hash(password)

            new_user = Customer(FullName=full_name, Email=email, Password=hashed_password)
            _db.session.add(new_user)
            _db.session.commit()

            return redirect(url_for('blueprint.login'))

        return SignupView().render('register.html')


    def login(self):
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']

            customer = Customer.query.filter_by(Email=email).first()

            if customer and check_password_hash(customer.Password, password):
                session['customer_id'] = customer.CustomerID
                return redirect(url_for('blueprint.dashboard'))

        return LoginView().render('login.html')


    def logout(slef):
        session.pop('customer_id', None)
        return redirect(url_for('blueprint.login'))