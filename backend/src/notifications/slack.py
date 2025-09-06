import os
import requests

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def send_slack_alert(message: str):
    if not SLACK_WEBHOOK_URL:
        print("⚠️ No Slack webhook URL found in environment")
        return
    payload = {"text": message}
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code != 200:
            print(f"⚠️ Slack error: {response.status_code}, {response.text}")
    except Exception as e:

        print(f"❌ Error al enviar alerta Slack: {e}")

