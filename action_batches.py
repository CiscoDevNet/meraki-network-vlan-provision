from time import sleep
import sys

import requests

base_url = 'https://api.meraki.com/api/v1'

def safe_api_call(method="",url="",json=None,headers=""):
    try:
        api_success = False
        while not api_success:
            print(method + " calling: " + url)
            response = requests.request(method, url, json=json, \
            headers=headers)
            if response.status_code == 429:
                print(f"API Rate Limit Hit: Retrying in {response.headers['Retry-After']} seconds")
                sleep(int(response.headers["Retry-After"]))
                print("retrying API call ...")
            elif response.status_code == 404:
                print("404 hit, but valid URL; retrying after 2 mins")
                sleep(120)
            elif response.status_code in [200,201,203,204]:
                api_success = True
                print(url + " called successfully")
                return response
            else:
                sys.exit("Exiting on error: " + str(response.status_code) + " " + response.text)
    except Exception as e:
        print(e)
        sys.exit(1)

def create_action_batch(api_key, org_id, confirmed=False, synchronous=False, actions=None):
    post_url = base_url+'/organizations/' + org_id + '/actionBatches'
    headers = {'X-Cisco-Meraki-API-Key': api_key, 'Content-Type': 'application/json'}

    payload = {
        'confirmed': confirmed,
        'synchronous': synchronous,
        'actions': actions,
    }
    response = safe_api_call(method="POST",url=post_url,json=payload, headers=headers)
    data = response.json() if response.ok else response.text
    return (response.ok, data)


def get_org_action_batches(api_key, org_id):
    get_url = base_url+'/organizations/' + org_id + '/actionBatches'
    headers = {'X-Cisco-Meraki-API-Key': api_key, 'Content-Type': 'application/json'}

    response = safe_api_call(method="GET",url=get_url,headers=headers)
    data = response.json() if response.ok else response.text
    return (response.ok, data)


def get_action_batch(api_key, org_id, batch_id):
    get_url =  base_url+'/organizations/' + org_id + '/actionBatches/' + batch_id
    headers = {'X-Cisco-Meraki-API-Key': api_key, 'Content-Type': 'application/json'}

    response = safe_api_call(method="GET",url=get_url,headers=headers)
    data = response.json() if response.ok else response.text
    return (response.ok, data)


def delete_action_batch(api_key, org_id, batch_id):
    delete_url = base_url+'/organizations/' + org_id + '/actionBatches/' + batch_id
    headers = {'X-Cisco-Meraki-API-Key': api_key, 'Content-Type': 'application/json'}

    response = safe_api_call(method="DELETE",url=delete_url,headers=headers)
    data = response.json() if response.ok else response.text
    return (response.ok, data)


def update_action_batch(api_key, org_id, batch_id, confirmed=False, synchronous=False):
    put_url = base_url+'/organizations/' + org_id + '/actionBatches/' + batch_id
    headers = {'X-Cisco-Meraki-API-Key': api_key, 'Content-Type': 'application/json'}

    payload = {
        'confirmed': confirmed,
        'synchronous': synchronous,
    }

    response = safe_api_call(method="PUT",url=put_url,json=payload, headers=headers)
    data = response.json() if response.ok else response.text
    return (response.ok, data)


# Helper function to check the completion status of an asynchronous action batch
def check_status(api_key, org_id, batch_id):
    (ok, data) = get_action_batch(api_key, org_id, batch_id)
    if ok and data['status']['completed'] and not data['status']['failed']:
        print('Action batch ' +  batch_id +  ' completed!')
        return 1
    elif ok and data['status']['failed']:
        print(data)
        return -1
    else:
        return 0


# Check until asynchronous action batch either completes or fails
def check_until_completed(api_key, org_id, batch_id, print_message=False):
    counter = 0
    while True:
        status = check_status(api_key, org_id, batch_id)
        if status == 1:
            return True
        elif status == -1:
            return False
        elif print_message:
            print('Action batch ' +  batch_id + 'processing... ' + str(99 - counter) + ' iterations')
            sleep(1)
            counter += 1
