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

# Google Sheets API Setup (Hardcoded Google Credentials)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = {
    "type": "service_account",
    "project_id": "contact-re-subscription",
    "private_key_id": "df625bc93a5539d6574b29d7163edfdf9020669e",
    "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCZ7WDFxbnbSxiY
6twLzfN9nnRQXHdHjMfc03HDpYessqevvN3AuJ3T1ZVXCt8TbLZlyKS6C8jx90YI
iy0PiJO1rbzFoiPfNi8p1bqzcVzDIN5eqlQFQffweMVxFEDIhkBMm8nguKf8uKWE
ElN1ViKlDIy12pmeK1/A8F/Y5wMwEGzEP+uAkj2YBTueUJSW9mfLf21INEOsGU5T
py6919BU/X3e8fHvqmPRjezAePD4V0xLyRUQCFgbNf/cZTEFmmqN6+5JqYGB2By9
z80YJJUgLm6vWa/UbxlBqZ7LdBKqXfMC/QxkHEbwUTjHgzpKjv8clW3DJRJ7udFB
Ve+/3jy9AgMBAAECggEAA3zxJk66x2fNz1FJnWyUPBc246K6G1Ot+5BAxanGdW/R
EEqn+CWbacipGmXkJRA1Ehl83So6J1gA/DkN00ExGNZrkD8g4H5vyh4vzl7JyTJf
0AIFtg90xqPPHZSiuFM4M2jJ3jFYpSxVm9lF5E9p/jti519L82NH8icuAo8txRNb
GLGAUx6Vf+ySn/OA6QDLKxRjhqL8A80ErgYx1y8WjqiRnv+sFdLnhZmPjke/uMH5
JBVcuvMCjn7FrNgbR47qEO6VMHgmVnZrlaUJ7AhvD7eYSCGSesD4Rqc7MGFIX2zP
67SEHosvb2yusQFlKrJ63F7Wciq0ReO1kuS4kFI7RQKBgQDT6JjUs2x8vSvjUbo+
FFK0RJIz8P5n1TouYt6R2wG5V1be6X43QQkq0nKURDJ/SrLlAgMfwvQgt6awv+Mb
isgZuVelRDB6DfFEczSD+6KzKCyruLMOtb32iL2fY8Ma4zSosjoQSes9V/n84EWN
vW8+zcFABfjWHOuTi2sjDTNGGwKBgQC59GFpa4wSp+C6cMf/uWq6ogRwqXIpTr5W
zJbToRkdvasJxv2JSbMCKJhRj2oLT/xqpNer6YeIe/9Xv0nXnL0am0lgs8fB+gvo
FOnqhSVjkF4XbWvCVTvx/M0cid0/EgH+a5xDMceYFr+gcjaPc9QnHOpVFO3bbG05
+GeljWMWBwKBgD3YeZpCT1xMfZ2XgaqSldyk0qK0KBu3wIY/NsQMzgEAu4rNTJfl
tD46M1SQXsiFzZZGsxC2/jb6Qnz9U9P6+hF/5VOHhjppDUwz71TBwSdWh0sK2b9m
TW3BVM5K+GtFel3tvkJ4wF4j6gLilYobinci586+r3QV9q8WFouhU6CXAoGBALap
yVqd642T3Rwnlz6ra50Dc+sbd+n90NlAxVQDpsFhQ/cpwnmurKoNKHrNrvSH0MMN
RFI55wn6C/ytCiNDczsEmVLlpu7z6ehDSvg1bGHeOZ83vCe8RFNT6kQDZRMEZHMA
UBJtfsv2ZKx+JPxLYnY9YC7NjU0CuFS+n0mvlkrXAoGBAIWiJVibN5bx4eajoXri
6mVFksFJ+lvSw5D6zqAVnMbCYS+bl4ObCwdOx0AS94JZW4dVA/RBPBZ/h+OcASpE
usGkBqeTABad0GD5QwTXT6A9cc+s7zbJHgzn2WB2s+xgbmbizOjttiJVnAPBwQtj
ZVNy6V9WD2dnXnz26yMpXDu7
-----END PRIVATE KEY-----""",
    "client_email": "contact-re-subscription@contact-re-subscription.iam.gserviceaccount.com",
    "client_id": "113077265641381114597",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/contact-re-subscription%40contact-re-subscription.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1RUyZAOSdtAMG74aa6qa9h3AGfXvz5UYxGeLlqPpzqqE").sheet1

# ActiveCampaign API Setup
AC_API_URL = os.environ.get("AC_API_URL")
AC_API_KEY = os.environ.get("AC_API_KEY")


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
