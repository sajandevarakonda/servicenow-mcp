import os
import requests
from datetime import datetime, timedelta

# Load credentials from environment variables
SERVICENOW_INSTANCE_URL = os.getenv('SERVICENOW_INSTANCE_URL')

# Log environment variables
print("ServiceNow Environment Variables:")
print(f"SERVICENOW_INSTANCE_URL: {os.getenv('SERVICENOW_INSTANCE_URL')}")
print(f"SERVICENOW_USERNAME: {os.getenv('SERVICENOW_USERNAME')}")
print(f"SERVICENOW_PASSWORD: {os.getenv('SERVICENOW_PASSWORD')}")
SERVICENOW_USERNAME = os.getenv('SERVICENOW_USERNAME')
SERVICENOW_PASSWORD = os.getenv('SERVICENOW_PASSWORD')

# Calculate date one month ago
one_month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

# Build query for P01 incidents in last month
query = f"priority=P01^opened_at>={one_month_ago}"
url = f"{SERVICENOW_INSTANCE_URL}/api/now/table/incident?sysparm_query={query}&sysparm_limit=10"

response = requests.get(
    url,
    auth=(SERVICENOW_USERNAME, SERVICENOW_PASSWORD),
    headers={"Accept": "application/json"}
)

if response.status_code == 200:
    incidents = response.json().get('result', [])
    print(f"Found {len(incidents)} P01 incidents in the last month:")
    for inc in incidents:
        print(f"Number: {inc['number']}, Short Description: {inc['short_description']}, Opened At: {inc['opened_at']}")
else:
    print(f"Failed to fetch incidents: {response.status_code} - {response.text}")
