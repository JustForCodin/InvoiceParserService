import os
from flask import *
from db.models import Invoice, InvoiceItem
from services.parse import InvoiceParser
from viewa.invoice_uploader_view import InvoiceUploaderView
from app import _db
import json


class InvoiceUploaderController:
    def add_invoice(self):
        return InvoiceUploaderView().render('upload.html')


    def upload_file(self):
        if request.method == 'POST':
            if 'image' not in request.files:
                return jsonify({'message': 'No file part'}), 400
            file = request.files['image']
            if file.filename == '':
                return jsonify({'message': 'No selected file'}), 499

            if file:
                file.save(os.path.join('uploads', file.filename))
                parser = InvoiceParser(
                    os.path.join('uploads', file.filename),
                    '/Users/macadmin/InvoiceParserService/nano_best.pt'
                )

                invoice_header, invoice_itmes = parser.invoice_to_dict()
                sorted_header, sorted_items = parser.sort_invoice_dict_by_keys(invoice_header, invoice_itmes)
                decoded_invoice_header = parser.decode_invoice_header(sorted_header)
                decoded_invoice_items = parser.decode_invoice_items(sorted_items)
                assembled_invoice = parser.assemble_invoice_data(decoded_invoice_header, decoded_invoice_items)
                final_invoice = parser.convert_to_mysql_format(assembled_invoice)
                print(f"FINAL INVOICE ==== {json.dumps(final_invoice, indent=4)}")

                new_invoice = Invoice()
                new_invoice.CustomerID = session.get('customer_id')

                try:
                    new_invoice.BillFrom = final_invoice['billFrom']
                except Exception as e:
                    new_invoice.BillFrom = "Unknown Sender"
                
                try:
                    new_invoice.BillTo = final_invoice["billTo"]
                except Exception as e:
                    new_invoice.BillTo = "Unknown Client"
                
                try:
                    new_invoice.InvoiceDate = final_invoice["invoiceDate"]
                except Exception as e:
                    new_invoice.InvoiceDate = "2022-07-01"

                try:
                    new_invoice.DueDate = final_invoice['dueDate']
                except Exception as e:
                    new_invoice.DueDate = "2023-11-12"

                _db.session.add(new_invoice)
                _db.session.commit()

                for item in final_invoice['items']:
                    new_item = InvoiceItem()
                    new_item.InvoiceID = new_invoice.InvoiceID

                    try:
                        new_item.ItemDescription = item['itemDescription']
                    except Exception as e:
                        new_item.ItemDescription = "[no description]"

                    try:
                        new_item.UnitPrice = item["unitPrice"]
                    except Exception as e:
                        new_item.UnitPrice = "0.0"

                    try:
                        new_item.Quantity = item["quantity"]
                    except Exception as e:
                        new_item.Quantity = "0.0"
                    
                    try:
                        new_item.LineTotal = item["lineTotal"]
                    except Exception as e:
                        new_item.LineTotal = "0.0"

                    _db.session.add(new_item)
                _db.session.commit()

                return jsonify({'message': 'File uploaded successfully'})