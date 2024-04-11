from dateutil.parser import parse
from ultralytics import YOLO
import tensorflow as tf
from PIL import Image
import pytesseract
import dateparser
import cv2
import ast


def group_items(invoice_items: dict) -> list:
    invoice_items_grouped = {}

    for key, value in invoice_items.items():
        if value not in invoice_items_grouped:
            invoice_items_grouped[value] = []
        invoice_items_grouped[value].append(key)

    grouped_list = []
    max_len = max(len(lst) for lst in invoice_items_grouped.values())
    for i in range(max_len):
        grouped_item = {}
        for key, value in invoice_items_grouped.items():
            if i < len(value):
                grouped_item[value[i]] = key
        grouped_list.append(grouped_item)
    return grouped_list


def is_date(string, fuzzy=False) -> bool:
    try: 
        parse(string, fuzzy=fuzzy)
        return True
    except ValueError:
        return False


def format_decimal(value: str) -> str:
    new_value = \
        value.replace(" ", "").replace("," , ".").replace("$", "") \
        .replace("€", "").replace("£", "").replace("₴", "") \
        .replace("¥", "").replace("₹", "").replace("₩", "")
    return new_value


def is_decimal(value: str) -> bool:
    try:
        float(value.strip())
        print(f"Value {value} is decimal")
        return True
    except:
        return False


def is_int(value: str) -> bool:
    try:
        int(value)
        return True
    except:
        return False
    

def is_currency(value: str) -> bool:
    if "$" in value or "€" in value \
        or "£" in value or "₴" in value or "¥" in value \
        or "¥" in value or "₹" in value or "₩" in value:
        return True
    return False


def is_mail(value: str) -> bool:
    if "@" in value:
        return True
    return False


class InvoiceParser:
    img_path: str
    model_path: str

    def __init__(self, img_path, model_path):
        self.img_path = img_path
        self.model_path = model_path


    def invoice_to_dict(self) -> dict:
        """
        Composes data stored in the trained model (predicted bboxes and their labels)
        in a dictionary.
        """

        model = YOLO(self.model_path)
        print(f"Invoice {self.img_path} loaded successfully.")

        invoice_img_data = cv2.imread(self.img_path, cv2.IMREAD_COLOR)
        result = model(invoice_img_data)
        invoice_header = {}
        invoice_items = {}

        for r in result:
            boxes = r.boxes 
            for box in boxes:
                # convert tensors encoding bboxes to lists
                # wrap them into strings and map to corresponding labels
                if not model.names[int(box.cls)] == 'generalText' and \
                    not model.names[int(box.cls)] == 'itemDescription' and \
                    not model.names[int(box.cls)] == 'quantity'    and \
                    not model.names[int(box.cls)] == 'unitPrice'   and \
                    not model.names[int(box.cls)] == 'lineTotal':
                    invoice_header[model.names[int(box.cls)]] = str(tf.Variable(box.xyxy[0]).numpy().tolist())

                if model.names[int(box.cls)] == 'itemDescription' or \
                    model.names[int(box.cls)] == 'quantity'   or \
                    model.names[int(box.cls)] == 'unitPrice'  or \
                    model.names[int(box.cls)] == 'lineTotal':
                    invoice_items[str(tf.Variable(box.xyxy[0]).numpy().tolist())] = model.names[int(box.cls)]
        return invoice_header, invoice_items
    

    def sort_invoice_dict_by_keys(self, invoice_header: dict, invoice_items) -> dict:
        # sort header in alphabetical order
        sorted_invoice_header = dict(sorted(invoice_header.items()))

        # sort items by x and y
        # sorted_invoice_items = dict(sorted(invoice_items.items(), key=lambda y: (y[0][1], y[0][3]), reverse=True))
        # sorted_invoice_items = dict(sorted(sorted_invoice_items.items(), key=lambda x: (x[0][0], x[0][2])))

        sorted_invoice_items = dict(sorted(invoice_items.items(), key=lambda y: (y[0][1], y[0][3]), reverse=True))
        sorted_invoice_items = dict(sorted(sorted_invoice_items.items(), key=lambda x: (x[0][0], x[0][2])))

        # split subdict into N chunks 
        # (smaller dicts) so each has {description: "text", qty: 2, price: 3, total: 4} structure
        # sorted_items_chunks = list(chunks(sorted_invoice_items))
        sorted_items_chunks = group_items(sorted_invoice_items)

        # join header and items to form resulting dict
        # sorted_invoice['items'] = sorted_items_chunks
        return sorted_invoice_header, sorted_items_chunks
    
    
    def decode_invoice_header(self, invoice_header: dict) -> dict:
        invoice_img_to_crop = Image.open(self.img_path)
        decoded_invoice_header = {}

        for key, value in invoice_header.items():
            # crop image by given coordinates
            cropped_image = invoice_img_to_crop.crop(tuple(ast.literal_eval(value)))
            cropped_image.convert("RGBA")
            # extract text from that image
            new_value = pytesseract.image_to_string(cropped_image, config='--psm 6')
            decoded_invoice_header[key] = new_value
        return decoded_invoice_header


    def decode_invoice_items(self, invoice_items: list) -> list:
        invoice_img_to_crop = Image.open(self.img_path)
        decoded_invoice_items = []

        for item in invoice_items:
            decoded_invoice_item = {}
            for key, value in item.items():
                key_image = invoice_img_to_crop.crop(ast.literal_eval(key))
                key_new = pytesseract.image_to_string(key_image, config='--psm 6')
                decoded_invoice_item[value] = key_new
            decoded_invoice_items.append(decoded_invoice_item)
        return decoded_invoice_items
    

    def assemble_invoice_data(self, invoiec_header: dict, invoice_items: list) -> dict:
        assembled_invoice = invoiec_header
        assembled_invoice["items"] = invoice_items
        return assembled_invoice


    def convert_to_mysql_format(self, decoded_invoice: dict) -> dict:
        for k, v in decoded_invoice.items():
            if '\n' in v:
                v = v.strip()
                decoded_invoice[k] = v
            if k == "dueDate" or k == "invoiceDate":
                v = dateparser.parse(v).strftime("%Y-%m-%d")
                decoded_invoice[k] = v
            if is_currency(v):
                new_value = format_decimal(v)
                decoded_invoice[k] = new_value

        for item in decoded_invoice["items"]:
            for key, val in item.items():
                if '\n' in val:
                    val = val.replace('\n', '')
                    item[key] = val
                if key == "unitPrice" or key == "quantity" or key == "lineTotal":
                    item[key] = format_decimal(val)
        return decoded_invoice

