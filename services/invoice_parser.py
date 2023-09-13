from simple_salesforce import Salesforce, SalesforceLogin, SFType
from flask import *
from datetime import timedelta
from utils.parse import InvoiceParser
import pandas as pd
import json
import os

record_id = ""

app = Flask(__name__)

@app.route('/')
def index():
    return '<h1>Hello! InvoiceParser Web Service is working!</h1>'

@app.route('/parsed-invoice', methods=['POST'])
def parse_invoice():
    # Connect to Salesforce org
    login_info = json.load(open("login.json"))
    username = login_info['username']
    password = login_info['password']
    security_token = login_info['security_token']
    # domain = "login"

    session_id, instance = SalesforceLogin(
        username=username, password=password,
        security_token=security_token
    )
    sf = Salesforce(instance=instance, session_id=session_id)


    files_ids = request.get_json(force=True)
    print(f"FILE IDS JSON  {files_ids} TYPE {type(files_ids)}")
    

    # Query invoice that user has just uploaded.
    soql_query = f"""
	SELECT ContentDocumentId, Title, FileExtension, VersionData 
	FROM ContentVersion 
	WHERE ContentDocumentId IN {str(files_ids).replace('[', '(').replace(']', ')')}
    AND IsLatest=True
	ORDER BY CreatedDate DESC
	"""

    print(f"[*] SOQL is: {soql_query}")

    response = sf.query(soql_query)
    records_list = response.get('records')
    next_record_url = response.get('nextRecordUrl')

    while not response.get('done'):
        response = sf.query_more(next_record_url, identifier_is_url=True)
        records_list.extend(response.get('records'))
        next_record_url = response.get('nextRecordUrl')

    df_records = pd.DataFrame(records_list)
    instance_name = sf.sf_instance
    attachments_path = "./AttachmentsDownload"

    invoice_jsonified = ""
    files_count = 0

    files = []
    # Download invoice
    for row in df_records.iterrows():
        invoice_url = row[1]['VersionData']
        record_id = row[1]['ContentDocumentId']
        file_name = record_id + row[1]['FileExtension']

        # if directory to store invoices wasn't created, create one
        if not os.path.exists(os.path.join(attachments_path, record_id)):
            os.makedirs(os.path.join(attachments_path, record_id))

        # Download invoice from org
        sf_request = sf.session.get(f"https://{instance_name}{invoice_url}",
                                headers=sf.headers
        )

        # Save as .pdf file
        with open(os.path.join(attachments_path, record_id, file_name), 'wb') as f:
            f.write(sf_request.content)
            f.close()
            print(f"==== DOWLOADED FILE {os.path.join(attachments_path, record_id, file_name)}")
            files_count += 1

        parser = InvoiceParser(os.path.join(attachments_path, record_id, file_name), '../best.pt')
        invoice_dict = parser.invoice_to_dict()
        invoice_dict_sorted = parser.sort_invoice_dict_by_keys(invoice_dict)
        decoded_invoice = parser.decode_keys(invoice_dict_sorted)
        files.append(decoded_invoice)
        print(f"[*] INVOICE JSON ==> {json.dumps(files)}")
    
    return json.dumps(files)