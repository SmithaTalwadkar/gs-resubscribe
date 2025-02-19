from flask import Flask, request, jsonify
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import time

# Initialize Flask app
app = Flask(__name__)

# Google Sheets API Setup using Environment Variable
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load Google credentials from environment variable
creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Open the Google Sheet
sheet = client.open("ActiveCampaign Contacts").sheet1

# ActiveCampaign API Setup
AC_API_URL = os.environ.get("AC_API_URL")  # Use Environment Variable
AC_API_KEY = os.environ.get("AC_API_KEY")  # Use Environment Variable

def resubscribe_contact(email):
    """Re-subscribe a contact using ActiveCampaign API."""
    headers = {
        "Api-Token": AC_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "contact": {
            "email": email,
            "status": 1  # 1 = Active (Subscribed)
        }
    }
    response = requests.post(AC_API_URL, json=data, headers=headers)
    return response.status_code, response.text


@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive ActiveCampaign Webhook and process contacts."""
    try:
        if not request.is_json:
            print("Request is not JSON")
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        print("Received JSON payload:", json.dumps(data, indent=2))  # Print payload

        contacts = data.get("contacts") or data.get("contact") or []
        if isinstance(contacts, dict):
            contacts = [contacts]

        if not contacts:
            print("No contacts found")
            return jsonify({"error": "No contacts provided"}), 400

        for contact in contacts:
            email = contact.get("email")
            if email:
                # Write contact to Google Sheets
                sheet.append_row([
                    email,
                    contact.get("first_name", ""),
                    contact.get("last_name", ""),
                    contact.get("phone", "")
                ])

                # Re-subscribe contact in ActiveCampaign
                status, response_text = resubscribe_contact(email)
                print(f"Re-subscribed: {email} - Status: {status} - Response: {response_text}")

        return jsonify({"message": "Contacts processed successfully"}), 200

    except Exception as e:
        print("Error occurred:", str(e))
        return jsonify({"error": str(e)}), 500
