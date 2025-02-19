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
        data = request.json
        contacts = data.get("contacts", [])

        for contact in contacts:
            email = contact.get("email")
            first_name = contact.get("first_name", "")
            last_name = contact.get("last_name", "")
            phone = contact.get("phone", "")

            if email:
                # Write contact to Google Sheets
                sheet.append_row([email, first_name, last_name, phone])

                # Re-subscribe contact in ActiveCampaign
                status, response_text = resubscribe_contact(email)
                print(f"Re-subscribed: {email} - Status: {status} - Response: {response_text}")

                time.sleep(1)  # Avoid rate limiting

        return jsonify({"message": "Contacts processed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
