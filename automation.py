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
sheet = client.open_by_key("YOUR_GOOGLE_SHEET_ID").sheet1  # Use Google Sheet ID

# ActiveCampaign API Setup
AC_API_URL = os.environ.get("AC_API_URL")
AC_API_KEY = os.environ.get("AC_API_KEY")

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

        # Get JSON payload and print it for debugging
        data = request.get_json()
        print("Received JSON payload:", json.dumps(data, indent=2))

        # Handle both single and multiple contacts
        contacts = data.get("contacts") or data.get("contact") or []
        if isinstance(contacts, dict):
            contacts = [contacts]

        if not contacts:
            print("No contacts found")
            return jsonify({"error": "No contacts provided"}), 400

        # Process each contact
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


@app.route('/test-google-sheets', methods=['GET'])
def test_google_sheets():
    """Test if Google Sheets connection works."""
    try:
        sheet.append_row(["Test Email", "First Name", "Last Name", "1234567890"])
        return jsonify({"message": "Google Sheets access successful"}), 200
    except Exception as e:
        print("Google Sheets Error:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/')
def home():
    """Root route for health check."""
    return "Webhook service is running!", 200


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Default to port 10000 for Render
    app.run(host="0.0.0.0", port=port, debug=True)  # Enable Debug Mode
