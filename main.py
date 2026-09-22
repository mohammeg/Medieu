import os
import requests
import gspread
from fastapi import FastAPI, Request, Response, BackgroundTasks
from google.oauth2.service_account import Credentials
from google import genai
from dotenv import load_dotenv

load_dotenv() 
app = FastAPI()

# --- CONFIGURATION (Load via Environment Variables) ---
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Initialize Gemini Client
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Initialize Google Sheets Client once globally
SHEET_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
sheets_creds = Credentials.from_service_account_file("credentials.json", scopes=SHEET_SCOPES)
gspread_client = gspread.authorize(sheets_creds)


# --- 1. FETCH AVAILABLE INVENTORY ---
def get_available_inventory() -> str:
    try:
        sheet = gspread_client.open("Real Estate").worksheet("Inventory")
        all_records = sheet.get_all_records()

        available_properties = [
            row for row in all_records
            if str(row.get("Status", "")).strip().lower() == "available"
        ]

        if not available_properties:
            return "No available properties at the moment."

        inventory_lines = [
            f"{idx}. Type: {item.get('Type')}, Location: {item.get('City/Area')}, "
            f"Bedrooms: {item.get('Bedrooms')}, Price: {item.get('Price')}, "
            f"Details: {item.get('Description')}"
            for idx, item in enumerate(available_properties, 1)
        ]
        return "\n".join(inventory_lines)

    except Exception as e:
        print(f"Error reading Google Sheets: {e}")
        return "Error fetching inventory."


# --- 2. MATCH USER QUERY WITH GEMINI ---
def generate_ai_reply(user_message: str, inventory_data: str) -> str:
    prompt = f"""
You are a helpful and polite real estate AI assistant for a local real estate agency.

Here is our current AVAILABLE property inventory:
---
{inventory_data}
---

Customer Inquiry: "{user_message}"

Instructions:
1. Recommend matching properties from the available inventory.
2. State details (Type, Location, Bedrooms, Price, Details) clearly and concisely.
3. If no matching property is found, politely inform the customer and suggest what is currently available.
4. Keep the reply concise and formatted for WhatsApp (use bold text or short bullet points). Reply in the same language as the inquiry (e.g., Arabic or English).
"""
    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Thank you for reaching out! Our team will get back to you shortly with options."


# --- 3. SEND WHATSAPP MESSAGE ---
def send_whatsapp_message(to_phone: str, text: str):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": text},
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"WhatsApp API delivery error: {e}")


# --- BACKGROUND WORKER ---
def process_incoming_message(sender_phone: str, user_text: str):
    inventory = get_available_inventory()
    reply_text = generate_ai_reply(user_text, inventory)
    send_whatsapp_message(sender_phone, reply_text)


# --- 4. FASTAPI WEBHOOK ENDPOINTS ---
@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(content="Verification failed", status_code=403)


@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()

    try:
        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                for msg in messages:
                    if msg.get("type") == "text":
                        sender_phone = msg.get("from")
                        user_text = msg.get("text", {}).get("body", "").strip()

                        # Dispatch task to background and reply 200 immediately
                        background_tasks.add_task(
                            process_incoming_message, sender_phone, user_text
                        )
    except Exception as e:
        print(f"Error parsing webhook payload: {e}")

    # Meta requires a rapid 200 OK response
    return {"status": "success"}
