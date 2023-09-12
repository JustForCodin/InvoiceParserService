from ultralytics import YOLO
import tensorflow as tf
from PIL import Image
import pytesseract
import itertools 
import json
import cv2
import ast

def chunks(data, SIZE=4):
    it = iter(data)
    for i in range(0, len(data), SIZE):
        yield {k:data[k] for k in itertools.islice(it, SIZE)}

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

        model = YOLO('yolov8x.yaml')
        model = YOLO(self.model_path)
        # image = '/Users/odrozd/Desktop/OCRdata/images/train/inv6-1.png'
        print(f"===== IMAGE: {self.img_path} =====")

        invoice_img_data = cv2.imread(self.img_path, cv2.IMREAD_COLOR)
        result = model(invoice_img_data)
        invoice_json = {}

        for r in result:
            boxes = r.boxes 
            for box in boxes:
                # convert tensors encoding bboxes to lists
                # wrap them into strings and map to corresponding labels
                if not model.names[int(box.cls)] == 'generalText':
                    invoice_json[str(tf.Variable(box.xyxy[0]).numpy().tolist())] = model.names[int(box.cls)]

        # print(json.dumps(invoice_json, indent=4))

        return invoice_json

    def sort_invoice_dict_by_keys(self, invoice_dict: dict) -> list:
        """
        Sorts invoice data (represented as dictionary) 
        by x and y coordinates of each element's key.
        """

        def group_items(sorted_invoice_dict: dict) -> dict:
            # extract key-value pairs having description, unitPrice, quantity and lineTotal values into subdict
            # split subdict into N chunks (smaller dicts) so each has {description: "text", qty: 2, price: 3, total: 4} structure

            # extract all items
            invoice_items_top = list(sorted_invoice_dict.values()).index("itemDescription")
            invoice_items_bot = ""
            try:
                invoice_items_bot = list(sorted_invoice_dict.values()).index("subtotal")
            except:
                invoice_items_bot = list(sorted_invoice_dict.values()).index("total")

            items = dict(itertools.islice(sorted_invoice_dict.items(), invoice_items_top, invoice_items_bot))

            items_json = {}
            for k, v in items.items():
                items_json[str(k)] = v

            # FOR DEBUG ONLY: display items in JSON format
            # print(f"items === {json.dumps(items_json, indent=4)}")
            # print(f"items_json_chunks === {json.dumps(list(chunks(items_json)), indent=4)}")

            # split all items into N subdictionaries with structure describen above.
            return list(chunks(items_json))

        sorted_invoice_dict = {} # copy original dict
        for k, v in invoice_dict.items():
            sorted_invoice_dict[tuple(ast.literal_eval(k))] = v

        # FOR DEBUG ONLY
        # print(f"==== unsorted items ===\n")
        # for k, v in sorted_invoice_dict.items():
        #   print(f"{k} ==> {v}")

        # sort elements by keys 
        sorted_invoice_dict = dict(sorted(sorted_invoice_dict.items(), key=lambda x: (x[0][0], x[0][2]))) # sort by x
        sorted_invoice_dict = dict(sorted(sorted_invoice_dict.items(), key=lambda y: (y[0][1], y[0][3]))) # sort by y
        sorted_invoice_dict["items"] = group_items(sorted_invoice_dict)
        
        # FOR DEBUG ONLY - display encoded sorted data in JSON FORMAT
        sorted_invoice_dict_jsonified = {}
        for k, v in sorted_invoice_dict.items():
            sorted_invoice_dict_jsonified[str(k)] = v
        # print(f"sorted encoded invoice === {json.dumps(sorted_invoice_dict_jsonified, indent=4)}")
        return sorted_invoice_dict

    # def resize_image(self, image, new_width):
    #   new_height = int(new_width * 3 / 4)
    #   img_to_resize = Image.open(image)
    #   resized_image = img_to_resize.resize((new_width, new_height))
    #   return resized_image


    def decode_keys(self, invoice_dict_sorted: dict) -> dict:
        """
        Decodes predicted fields in incoming invoice. Keys are represented as tuples of bboxes coordinates/
        Pytesseract is used to crop incoming invoice image by keys and scan all the text in cropped image.
        Then, extracted text is used as a new key.
        """

        invoice_img_to_crop = Image.open(self.img_path)
        invoice_items = []
        decoded_invoice = {}
        decoded_invoice_items = []
        # print("==== SORTED ITEMS ====")
        cnt = 0 
        for key, value in invoice_dict_sorted.items():
            if key == "items":
                # extract item objects
                for item in value:
                    invoice_items.append(item)
                break

            # decode general info
            key = tuple(key) # get coordinates
            key_image = invoice_img_to_crop.crop(key) # crop image by given coordinates
            key_image.convert("RGBA")
            key_new = pytesseract.image_to_string(key_image, config='--psm 6') # extract text from that image
            decoded_invoice[value] = key_new # flip key and value to get appropriate structure.

            # FOR DEBUG ONLY  
            # print(f"{key_new} {key} {value}".split("\n"))

        # same for items
        for item in invoice_items:
            decoded_invoice_item = {}
            for key, value in item.items():
                key = ast.literal_eval(key)
                key_image = invoice_img_to_crop.crop(key)
                key_new = pytesseract.image_to_string(key_image, config='--psm 6')
                decoded_invoice_item[value] = key_new
            decoded_invoice_items.append(decoded_invoice_item)

        decoded_invoice["items"] = decoded_invoice_items
        # print(f"decoded_invoice_items === {decoded_invoice_items}")
        # print(f"decoded_invoice === {decoded_invoice}")
        # print(json.dumps(decoded_invoice, indent=4))
        del invoice_dict_sorted
        return decoded_invoice

# parser = InvoiceParser(
#     # '/Users/odrozd/Desktop/abstract-black-invoice-template-design_1017-15046.png',
#     'images/test002.png',
#     '/Users/odrozd/Desktop/best.pt'
# )
# invoice_dict = parser.invoice_to_dict()
# invoice_dict_sorted = parser.sort_invoice_dict_by_keys(invoice_dict)
# decoded_invoice = parser.decode_keys(invoice_dict_sorted)
# print(json.dumps(decoded_invoice, indent=4))
