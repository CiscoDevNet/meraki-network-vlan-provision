import json
import random
import sys
import os
import getopt
from action_batches import create_action_batch, check_until_completed
from time import sleep
import csv
import meraki

dashboard = meraki.DashboardAPI()

def check_batch_completion(org,batch_id):
    counter = 0
    while True:
        batch = dashboard.organizations.getOrganizationActionBatch(org,batch_id)
        if batch['status']['completed'] and not batch['status']['failed']:
            print('Action batch ' +  batch_id +  ' completed!')
            break
        elif batch['status']['failed']:
            print(batch)
            break
        else:
            print('Action batch ' +  batch_id + 'processing... ' + str(99 - counter) + ' iterations')
            sleep(1)
        counter += 1

def create_networks_and_assign_devices(org):
    network_actions=[]
    with open('meraki_config.csv', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        header = True

        for row in csv_reader:
            if header:
                print(f'Column names are {", ".join(row)}')
                header = False
            
            print(row["Network Name"])
            action = {
                'name': row["Network Name"],
                'type': 'appliance switch wireless camera systemsManager',
                'tags' : [row["Tag"]],
                    "productTypes": [
                        "appliance",
                        "switch",
                        "camera",
                        "wireless"
                    ]
            }
            network_actions.append({
                'resource': '/organizations/' + org + '/networks',
                'operation': 'create',
                'body': action
            })

            
        batch = dashboard.organizations.createOrganizationActionBatch(org,network_actions,confirmed=True,synchronous=False)
        check_batch_completion(org,batch["id"])

        print("created all networks done!")

    # Get the new network ID so we can add the devices
    networks = dashboard.organizations.getOrganizationNetworks(org)

    device_actions=[]
    with open('meraki_config.csv', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        header = True 

        for row in csv_reader:
            if header:
                print(f'Column names are {", ".join(row)}')
                header = False

            for network in networks:
                if network["name"] == row["Network Name"]:
                    network = network["id"] 
                    
                    device_list = row['Devices']
                    device_list = device_list.replace(";", ",")
                    device_list = device_list.split(",")
                    # add devices from .csv file
                    device_actions.append(
                    {
                        'resource': '/networks/' + network + '/devices',
                        'operation': 'claim',
                        'body': {
                            'serials': device_list
                        }
                    })

    batch = dashboard.organizations.createOrganizationActionBatch(org,device_actions,confirmed=True,synchronous=False)
    check_batch_completion(org,batch["id"])

    with open('meraki_config.csv', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        header = True

        for row in csv_reader:
            if header:
                print(f'Column names are {", ".join(row)}')
                header = False
 
            for network in networks:
                if network["name"] == row["Network Name"]:
                    network = network["id"] 
                    if int(row["Number_VLANS"]) > 0:
                        dashboard.appliance.updateNetworkApplianceVlansSettings(network,vlansEnabled=True)
                        network_vlan_actions = []
                        for number in range(int(row["Number_VLANS"])):
                            network_vlan_actions.append({
                                "resource": f"/networks/{network}/vlans",
                                "operation": "create",
                                "body": {
                                    "id": number+2,
                                    "name": f"VLAN {number+2}",
                                    "applianceIp": f"{row['VLAN_subnet']}.{number+2}.1",
                                    "subnet": f"{row['VLAN_subnet']}.{number+2}.0/24"
                                }
                            })

                        batch = dashboard.organizations.createOrganizationActionBatch(org,network_vlan_actions,confirmed=True,synchronous=False)
                        check_batch_completion(org,batch["id"])

def get_org_by_choice():
    # Get the new network ID so we can add the devices
    orgs = dashboard.organizations.getOrganizations()

    for org in orgs:
        print(org["name"])

    org_friendly_name = input("Enter the Organization: ")

    for org in orgs:     
        if org["name"] == org_friendly_name:
            return org["id"]
        else:
            print("Org not found!")
    
    return "Org not found"


def delete_networks(org):
    # Get the new network ID so we can add the devices
    networks = dashboard.organizations.getOrganizationNetworks(org)
    
    device_actions=[]
    network_actions=[]
    with open('meraki_config.csv', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        header = True

        for row in csv_reader:
            if header:
                print(f'Column names are {", ".join(row)}')
                header = False
 
            for network in networks:
                if network["name"] == row["Network Name"]:
                    network = network["id"] 
                    devices = dashboard.networks.getNetworkDevices(network)
                    for device in devices:
                        device_actions.append(
                        {
                            'resource': '/networks/' + network + '/devices',
                            'operation': 'remove',
                            'body': {
                                'serial': device["serial"]
                            }
                        })


                    network_actions.append(
                        {
                            'resource': '/networks/' + network,
                            'operation': 'destroy'
                        })

    if len(device_actions) > 0:
        batch = dashboard.organizations.createOrganizationActionBatch(org,device_actions,confirmed=True,synchronous=False)
        check_batch_completion(org,batch["id"])

    if len(network_actions) > 0: 
        batch = dashboard.organizations.createOrganizationActionBatch(org,network_actions,confirmed=True,synchronous=False)
        check_batch_completion(org,batch["id"])

     

if __name__ == "__main__":
    org = get_org_by_choice()


    opts, args = getopt.getopt(sys.argv[1:], "hcd", ["create", "delete"])


    for opt, arg in opts:
        if opt == "-h":
            print("meraki_network_vlan_provisioning.py -c for create \n")
            print("meraki_network_vlan_provisioning.py -d for delete \n")
            sys.exit()
        elif opt in ("-c", "--create"):
            create_networks_and_assign_devices(org)
        elif opt in ("-d", "--delete"):
            delete_networks(org)



