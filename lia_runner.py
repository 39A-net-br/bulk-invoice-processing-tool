import requests
import os
import json
import time
import csv
import glob
from dotenv import load_dotenv

load_dotenv(override=True, dotenv_path=".env")

class LIARunner:
    def __init__(self, invoices_path):
        self.invoices_path = os.path.abspath(invoices_path)
        self.base_url = os.getenv("BASE_URL")
        self.username = os.getenv("USERNAME")
        self.password = os.getenv("PASSWORD")
        self.batch_size = os.getenv("BATCH_SIZE")
        self.get_token()
        
        self.run()
    
    def get_token(self, refresh=False):
        if refresh and time.time() < self.refresh_expiration:
            headers = {"Authorization": f"Bearer {self.refresh_token}"}
            response = requests.post(f"{self.base_url}/refresh_token", headers=headers)
        else:
            auth = {'username': self.username, 'password': self.password}
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            response = requests.post(f"{self.base_url}/token", data=auth, headers=headers)
            
        token_response = json.loads(response.text)
        self.token = token_response['access_token']
        self.refresh_token = token_response['refresh_token']
        self.token_expiration = time.time() + token_response["expires_in"] - 1
        self.refresh_expiration = time.time() + token_response["refresh_expires_in"] - 1
    
    def submit_invoice(self, invoice_path):
        if time.time() > self.token_expiration:
            self.get_token(refresh=True)
        invoice_name = invoice_path.split("/")[-1]
        ext = invoice_name.split(".")[-1]
        invoice = {'file': (invoice_name, open(invoice_path, 'rb'), f'application/{ext}')}
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{self.base_url}/v5/upload_fatura", headers=headers, files=invoice)
        print(response)
        json_response = json.loads(response.text)
        
        return json_response['id_fatura']
        
    def get_result(self, id_fatura):
        if time.time() > self.token_expiration:
            self.get_token(refresh=True)
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/v5/find-fatura/{id_fatura}", headers=headers)
        result = json.loads(response.text)
        
        if 'Data' in result:
            result = {'status': "success", 'response': result['Data']['Result']}
        elif 'detail' in result:
            return {'status': "fail", 'message': result['detail']}
        elif result['status'] == "The requested invoice is currently ongoing":
            return {'status': "wait"}
        else:
            return {'status': "fail", 'message': result['status']}
        
        if 'Historic' in result:
            result['response']['Historic'] = json.dumps(result['response']['Historic'])
        
        return result
    
    def flatten_json(self, json, parent_key="", sep="."):
        items = []
        for k, v in json.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_json(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def build_csv(self, results, sub_set="full"):
        columns = set()
        for result in results:
            columns.update(result[2].keys())
        columns = sorted(columns)
        
        columns.insert(0, "FilePath")
        columns.insert(0, "LIA-ID")
        columns.insert(0, "StatusMessage")
        
        rows = []
        for result in results:
            row = {"StatusMessage": result[3], "LIA-ID": result[1], "FilePath": result[0]}
            row.update(result[2])
            rows.append(row)
        
        with open(f"responses_{sub_set}.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
    
    def run(self):
        invoices = glob.glob(f"{self.invoices_path}/*")
        sets = len(invoices) // self.batch_size
        if len(invoices) % self.batch_size > 0:
            sets += 1
        full_results = []
        for set in range(sets):
            print(f"CURRENT BATCH: {set}\n{100*'-'}")
            results = []
            upper = -1 if set == sets else (set+1)*self.batch_size
            for invoice in invoices[set*self.batch_size:upper]:
                print(f"SUBMITTING: {invoice}")
                result = []
                result.append(invoice.split("/")[-1])
                try:
                    result.append(self.submit_invoice(invoice))
                except:
                    result.append("[FAILURE]")
                results.append(result)
            for i in range(len(results)):
                print(f"RETRIEVING: {invoices[set*self.batch_size+i]} (ID: {results[i][1]})")
                if results[i][1] == "[FAILURE]":
                    invoice_result = {'status': "fail", 'message': "Failed to upload file"}
                else:
                    invoice_result = {'status': "wait"}
                    retries = 0
                    while invoice_result['status'] == "wait":
                        invoice_result = self.get_result(results[i][1])
                        if invoice_result['status'] == "wait":
                            time.sleep(20)
                            retries += 1
                            if retries >= 10:
                                invoice_result = {'status': "fail", 'message': "timeout"}
                if invoice_result['status'] == "fail":
                    results[i].append({})
                    results[i].append(f"[FAILURE] Err. Msg.: {invoice_result['message']}")
                else:
                    flattened = self.flatten_json(invoice_result['response'])
                    results[i].append(flattened)
                    results[i].append("[SUCCESS]")
                full_results.append(results[i])
            self.build_csv(results, set)
        self.build_csv(full_results)
        
        