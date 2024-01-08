import os, requests, json, uuid, time
import glob, csv
import pandas as pd

BASE_URL = "https://api.mouser.com/api/v1.0"


''' USER VARIABLES - CHANGE VALUES HERE '''
ENVIRONMENT_VARIABLE_API_KEY_NAME = "MOUSER_API_KEY"    # name of your environment variable (if you need another name for some reason on your system)

CSV_MOUSER_COLUMN_NAME = "MFN"                       # how you named your column
CSV_DELIMITER = ","                                     # the delimiter of your .csv-file
                                    
API_TIMEOUT_MAX_RETRIES = 10                            # max retries if api decides to return errors -> possibly due to my dataprocessing?
API_TIMEOUT_SLEEP_S = 2                                 # wait time between retries in seconds

''' mouser API request skeleton '''
class MouserAPIRequest:

    url = None
    api_url = None
    method = None
    body = {}
    response = None
    api_key = None

    name = ''
    allowed_methods = ['GET', 'POST']
    operation = None
    operations = {}

    def __init__(self, operation, body={}):
        self.operation = operation
        (method, url) = self.operations.get(self.operation, ('', ''))

        self.api_url = BASE_URL + url
        self.method = method
        self.body = body

        try:
            self.api_key = os.environ[ENVIRONMENT_VARIABLE_API_KEY_NAME]
            self.url = f"{self.api_url}?apiKey={self.api_key}"
        except KeyError:
            raise ValueError("\"MOUSER_API_KEY\" environment variable not found! \n\n**Make sure to add your MOUSER_API_KEY to your environment variables!**")

        if operation not in self.operations:
            print(f'[{self.name}]\tInvalid Operation')
            print('-' * 10)
            return None

    def get(self, url):
        response = requests.get(url=url)
        return response

    def post(self, url, body):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        response = requests.post(url=url, data=body, headers=headers)
        return response.text

    def run(self):
        print(f'{self.method}, {self.body}')
        if self.method == 'GET':
            self.response = self.get(self.url)
        elif self.method == 'POST':
            self.response = self.post(self.url, self.body)

        self.print_response() # print response
        return len(json.loads(self.response)["Errors"]) == 0 # if errors in response are empty, everything is fine

    def get_response(self):
        if self.response is not None:
            try:
                return json.loads(self.response)
            except json.decoder.JSONDecodeError:
                return self.response
        return {}

    def print_response(self):
        print(json.dumps(self.get_response(), indent=4, sort_keys=True))

''' api request class implementations '''
class MouserCartRequest(MouserAPIRequest):
    name = 'Cart'
    operations = {
        'get': ('GET', '/cart'),
        'update': ('POST', '/cart'),
        'insertitem': ('POST', '/cart/items/insert'),
        'updateitem': ('POST', '/cart/items/update'),
        'removeitem': ('POST', '/cart/item/remove'),
    }   
class MouserOrderRequest(MouserAPIRequest):
    name = 'Order'
    operations = {
        'get': ('GET', '/order'),
        'create': ('POST', '/order'),
        'getcurrencies': ('GET', '/order/currencies'),
        'getcountries': ('GET', '/order/countries'),
        'getquery': ('POST', 'order/options/query')
    }  


class BOMHandler:

    BOM_files = [] # all found bom files
    target_headers = [CSV_MOUSER_COLUMN_NAME, "Qty", "Reference(s)"] # target headers
    data_array = []

    def __init__(self, dir_path="", target_headers=target_headers):
        if (dir_path == ""):
            self.m_dir_path = os.getcwd()
            self.data_array = {header: [] for header in target_headers}

    def get_bom_files(self, dir_path=""):
        if(dir_path == ""):
            dir_path = self.m_dir_path
        self.BOM_files = glob.glob(os.path.join(dir_path, '*.csv'))
        return self.BOM_files
    
    def summerize_sorted_items(self, items):
        def get_numerical_part(element):
                return int(''.join(filter(str.isdigit, element)))
        
        ranges = []
        start = end = items[0]

        for i in range(1, len(items)):
            current_num = get_numerical_part(items[i])
            prev_num = get_numerical_part(items[i-1])

            if current_num - prev_num == 1 and items[i][0] == items[i-1][0]:
                end = items[i]
            else:
                if get_numerical_part(start) == get_numerical_part(end):
                    ranges.append(start)
                else:
                    ranges.append(f"{start}-{end}")
                start = end = items[i]

        if get_numerical_part(start) == get_numerical_part(end):
            ranges.append(start)
        else:
            ranges.append(f"{start}-{end}")

        return ", ".join(ranges)       

    def process_bom_file(self, bom_file, target_headers=target_headers):       

        header_row_index = None

        with open(bom_file, 'r') as f:
            csv_reader = csv.reader(f, delimiter=CSV_DELIMITER)
            for idx, row in enumerate(csv_reader):
                if all(header in row for header in target_headers):
                    header_row_index = idx # find row with target headers

        if header_row_index is not None:
            df = pd.read_csv(self.BOM_files[0], skiprows=header_row_index) # read csv, starting after target headers
            for header in target_headers:
                df[header] = df[header].astype(str).str.strip()     # clear white spaces
                self.data_array[header].extend(df[header].tolist()) # use extend to not get double lists

            # note that the CustomerPartNumber given by Reference(s) must be a string and not exceed 22 characters
            for idx, reference in enumerate(self.data_array[target_headers[2]]):  
                temp = self.summerize_sorted_items(str(reference).split(", "))[:21]       
                if(len(temp)>=21):
                    print(f'{idx}, \"{temp}\" exceeds maximum of 21 characters -> CustomerPartNumber will be cut off at 21th character!') 
                self.data_array[target_headers[2]][idx] = self.summerize_sorted_items(str(reference).split(", "))[:21]
                

            # print(self.data_array)
            return self.data_array

class MouserOrderClient:
    # specify the field name you used to store all manifacturer names, at the moment ONLY mouser part numbers are working
    search_strings = [CSV_MOUSER_COLUMN_NAME]
    # specify unwanted strings like "DNF" to be removed from the parts list
    # @note "DNF" ect. should NOT be specified as part number, please consider removing it, rather than specifying it here.
    # this is just a precaution to be able to generate a BOM, without modifying the KiCAD project itself.
    banned_strings = ["DNF", "None"]    

    def __init__(self):
        pass

    def process_request(self, request_type, operation, body={}):
        if request_type == "cart":
            return MouserCartRequest(operation, body).run()


    def order_parts_from_data_array(self, data_array):
        parts_json = [] # json body buffer

        headers = [] # get headers form data array
        for header in data_array:
            headers.append(header)

        df = pd.DataFrame(data_array)    
        for idx, row in df.iterrows():
            parts_json.append({'MouserPartNumber': row[headers[0]], 'Quantity': int(row[headers[1]]), 'CustomerPartNumber':row[headers[2]]})

        cart_uuid = uuid.uuid4()
        body = f"{{'CartKey': {cart_uuid}, 'CartItems': {parts_json}}}"  
        return self.process_request('cart', 'insertitem', body=body)

def main():
    success = False
    count = 0

    while count < API_TIMEOUT_MAX_RETRIES and not success:
        client = MouserOrderClient()
        bom_handler = BOMHandler()
        bom_handler.get_bom_files()
        bom_handler.process_bom_file(bom_handler.BOM_files[0])
        success = client.order_parts_from_data_array(bom_handler.data_array)
        count+=1
        if not success:
            time.sleep(API_TIMEOUT_SLEEP_S)

    print(f"tries:{count} - success: {success}")
             
if __name__ == "__main__":
    main()

