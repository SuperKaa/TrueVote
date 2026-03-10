from nicegui import ui, app
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("FASTAPI_URL")

"""function for get api requests"""

def api_get(endpoint, params=None):
    try:
        url = f"{BASE_URL}{endpoint}/{API_KEY}"
        response = requests.get(url, params=params, timeout=15)
        return response.json()
    
    except Exception as e:
        print(f"get error with {endpoint}: {e}")

        return None

"""function for post api requests"""

def api_post(endpoint, data):
    try:
        url = f"{BASE_URL}{endpoint}/{API_KEY}"

        response = requests.post(url, json=data, timeout=15)
        return response.json()
    
    except Exception as e:
        print(f"post error {endpoint}: {e}")

        return None

"""function for checking true or false"""

def is_true(val):
    if val == True:
        return True
    
    if isinstance(val, str):
        return val.lower() == "true"
    
    if isinstance(val, dict):
        return val.get("status") == "success" or val.get("success") == True
    
    return False

"""function for logging out"""

def do_logout():
    app.state.user = None
    app.state.user_email = None
    app.state.user_id = None
    ui.notify("logged out", color="positive")
    ui.navigate.to("/")
