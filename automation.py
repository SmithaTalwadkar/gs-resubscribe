from flask import Flask, request, jsonify
import os
import json
import threading
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import time

# Initialize Flask app
app = Flask(__name__)

# Google Sheets API Setup using Environment Variable
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1RUyZAOSdtAMG74aa6qa9h3AGfXvz5UYxGeLlqPpzqqE").sheet1

# ActiveCampaign API Setup
AC_API_URL = os.environ.get("AC_API_URL")  # Use the environment variable name
AC_API_KEY = os.environ.get("AC_API_KEY")  # Use the environment variable name


def resubscribe_contact(email):
    """Re-subscribe a contact using ActiveCampaign API."""
    try:
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
    except Exception as e:
        print(f"Error while re-subscribing {email}: {str(e)}")
        return 500, str(e)


def process_contacts(data):
    """Process contacts asynchronously."""
    try:
        # Handle both array and single object
        contacts = data.get("contacts") or data.get("contact") or data
        if isinstance(contacts, dict):
            contacts = [contacts]

        for contact in contacts:
            email = contact.get("email") or contact.get("contact_email")
            if email:
                # Handle different name formats
                first_name = contact.get("first_name") or contact.get("firstName") or ""
                last_name = contact.get("last_name") or contact.get("lastName") or ""
                phone = contact.get("phone") or contact.get("contact_phone") or ""

                try:
                    # Write contact to Google Sheets
                    sheet.append_row([email, first_name, last_name, phone])

                    # Re-subscribe contact in ActiveCampaign
                    status, response_text = resubscribe_contact(email)
                    print(f"Re-subscribed: {email} - Status: {status} - Response: {response_text}")

                except Exception as e:
                    print(f"Error processing contact {email}: {str(e)}")

    except Exception as e:
        print("Error occurred during contact processing:", str(e))


@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive ActiveCampaign Webhook and respond immediately."""
    try:
        # Print incoming headers
        print("Incoming Headers:", dict(request.headers))

        if not request.is_json:
            print("Request is not JSON")
            print("Request Data (Raw):", request.data.decode())
            return jsonify({"error": "Request must be JSON"}), 400

        # Print JSON payload (use force=True to parse even if Content-Type is incorrect)
        data = request.get_json(force=True, silent=True)
        if data is None:
            print("JSON payload is None or invalid")
            print("Request Data (Raw):", request.data.decode())
            return jsonify({"error": "Invalid JSON payload"}), 400

        print("Received JSON payload:", json.dumps(data, indent=2))

        # Process contacts in a separate thread
        threading.Thread(target=process_contacts, args=(data,)).start()

        # Respond immediately to ActiveCampaign
        return jsonify({"message": "Webhook received and processing started"}), 200

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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
