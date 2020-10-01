# meraki-network-vlan-provision
Python script that creates networks, adds devices, and creates vlans in Meraki based on input from a .csv file

## Requirements

* Python 3.6+
* Administrator access to Meraki Dashboard

## To run

Data is read from meraki_config.csv.  Columns are delimiated with comma and devices are delimited with semi-colon.  VLAN_subnet column allows you to dictate the IP address space the VLANs will be created in.  Those VLANS will be created incrementally and reference back to the MX assigned to the network. **NOTE** to add vlans an MX MUST be assigned to the network.  If the network does not include an MX device, set the Number_VLANS to 0 for that row.  Once the meraki_config.csv file is complete and the virutal environment is created:

### To create networks
```bash
pip install -r requirements.txt
export MERAKI_DASHBOARD_API_KEY=<your api key>
python meraki_network_vlan_provision.py -c
```

### To delete all networks
```bash
pip install -r requirements.txt
export MERAKI_DASHBOARD_API_KEY=<your api key>
python meraki_network_vlan_provision.py -d
```



