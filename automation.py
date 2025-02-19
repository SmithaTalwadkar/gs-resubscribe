from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import time

app = Flask(__name__)

# Google Sheets API Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google-credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("ActiveCampaign Contacts").sheet1

# ActiveCampaign API Setup
AC_API_URL = "https://chop.api-us1.com"
AC_API_KEY = "0469ca239ca1c379f57ddfaf5079c5abeb4acebc2b12d3562525ff6c2c9486d4ba29a5ac"

def resubscribe_contact(email):
    """Re-subscribe contact using ActiveCampaign API."""
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
    app.run(host="0.0.0.0", port=5000)
