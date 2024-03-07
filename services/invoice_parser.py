from flask import *
from utils.parse import InvoiceParser
from utils.db import Customer, Invoice, InvoiceItem, _db
from utils.hash_gen import generate_password_hash, check_password_hash
import os
import json

app = Flask(__name__, template_folder='../templates')

UPLOAD_FOLDER = 'uploads'   
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Alex120490@localhost/invoice_parser_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'DbR228h321q765rD3Tzxc1'
_db.init_app(app)

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'image' not in request.files:
            return jsonify({'message': 'No file part'}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({'message': 'No selected file'}), 499

        if file:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            parser = InvoiceParser(
                os.path.join(app.config['UPLOAD_FOLDER'], file.filename),
                '/Users/macadmin/InvoiceParserService/nano_best.pt'
            )

            invoice_dict = parser.invoice_to_dict()
            invoice_dict_sorted = parser.sort_invoice_dict_by_keys(invoice_dict)
            decoded_invoice = parser.decode_keys(invoice_dict_sorted)
            final_invoice = parser.convert_to_mysql_format(decoded_invoice)
            print(json.dumps(final_invoice, indent=4))

            # new_invoice = Invoice(
            #     CustomerID=session.get('customer_id'),
            #     BillFrom=final_invoice['billFrom'],
            #     BillTo=final_invoice['billTo'],
            #     InvoiceDate=final_invoice['invoiceDate'],
            #     DueDate=final_invoice['dueDate']
            # )
            new_invoice = Invoice()
            new_invoice.CustomerID = session.get('customer_id')
            try:
                new_invoice.BillFrom = final_invoice['billFrom']
            except:
                new_invoice.BillFrom = "Unknown Sender"
            
            try:
                new_invoice.BillTo = final_invoice["billTo"]
            except:
                new_invoice.BillTo = "Unknown Client"
            
            try:
                new_invoice.InvoiceDate = final_invoice["invoiceDate"]
            except:
                new_invoice.InvoiceDate = "2022-07-01"
            
            try:
                new_invoice.DueDate = final_invoice['dueDate']
            except:
                new_invoice.DueDate = "2023-11-12"

            print(f"Invoice {new_invoice.InvoiceID} was inserted to BD.")
            _db.session.add(new_invoice)
            _db.session.commit()

            new_item = InvoiceItem()
            new_item.InvoiceID = new_invoice.InvoiceID
            for item in final_invoice['items']:
                # new_item = InvoiceItem(
                #     InvoiceID=new_invoice.InvoiceID,
                #     ItemDescription=item['itemDescription'],
                #     UnitPrice=item['unitPrice'],
                #     Quantity=item['quantity'],
                #     LineTotal=item['lineTotal']
                # )
                
                try:
                    new_item.ItemDescription = item['itemDescription']
                except:
                    new_item.ItemDescription = "[no description]"

                try:
                    new_item.UnitPrice = item["unitPrice"]
                except:
                    new_item.UnitPrice = "0.0"
                
                try:
                    new_item.Quantity = item["quantity"]
                except:
                    new_item.Quantity = "0.0"
                
                try:
                    new_item.LineTotal = item["lineTotal"]
                except:
                    new_item.LineTotal = "0.0"

                _db.session.add(new_item)
                print(f"[+] Item {new_item.ItemID} was inserted to DB.")
            _db.session.commit()

            return jsonify({'message': 'File uploaded successfully'})


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        new_user = Customer(FullName=full_name, Email=email, Password=hashed_password)
        _db.session.add(new_user)
        _db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        customer = Customer.query.filter_by(Email=email).first()

        if customer and check_password_hash(customer.Password, password):
            session['customer_id'] = customer.CustomerID
            return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'customer_id' in session:
        customer_id = session['customer_id']
        customer = Customer.query.get(customer_id)
        invoices = customer.invoices
        return render_template('dashboard.html', customer=customer, invoices=invoices)

    return redirect(url_for('login'))