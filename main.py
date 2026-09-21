import os
import requests
import gspread
from fastapi import FastAPI, Request, Response
from oauth2client.service_account import ServiceAccountCredentials
from google import genai

app = FastAPI()

# --- CONFIGURATION ---
VERIFY_TOKEN = "myestate"
WHATSAPP_TOKEN = "EAAPHdN5JhgABSvJruoJZAidrcNIMZByNTcCZAZBpDDpO1rdQGULNX408mDxoDsctdHzvIT2HrZBDaK5zkqHFPu3UToWp7GZBuYgFNjKCrZCMJLah4F41aVbqYSvMMc1tZBwF64PVGjZAYJ5t9xZC73rfZBV3nGF9pTd1jT8h2A2pizgqD2IZCUZBb5gKZCwxI19DbYZAQ6v0iY2SGTQ0q0hCUnVTlsMz47uzhxsdi4YZCA1D8jFm"
PHONE_NUMBER_ID = "1234328209774020"
GEMINI_API_KEY = "AQ.Ab8RN6JemqiiRP3K0fCC1Km_Qx9nUappryi4KlFY1S8C5DTFbg"

# Initialize Gemini Client
ai_client = genai.Client(api_key=GEMINI_API_KEY)


# --- 1. FETCH AVAILABLE INVENTORY FROM GOOGLE SHEETS ---
def get_available_inventory() -> str:
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        
        # Open "Real Estate" sheet and select "Inventory" tab
        sheet = client.open("Real Estate").worksheet("Inventory")
        all_records = sheet.get_all_records()
        
        # Filter for "Available" properties only
        available_properties = [
            row for row in all_records 
            if str(row.get("Status", "")).strip().lower() == "available"
        ]
        
        # Format inventory into a readable string for Gemini
        inventory_text = ""
        for idx, item in enumerate(available_properties, 1):
            inventory_text += (
                f"{idx}. Type: {item.get('Type')}, Location: {item.get('City/Area')}, "
                f"Bedrooms: {item.get('Bedrooms')}, Price: {item.get('Price')}, "
                f"Details: {item.get('Description')}\n"
            )
            
        return inventory_text if inventory_text else "No available properties at the moment."
        
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
1. Analyze the customer inquiry and recommend the top matching option(s) from the available inventory.
2. If matching properties exist, state their details (Type, Location, Bedrooms, Price, Details) clearly in a concise, friendly text message.
3. If no matching property is found, politely inform the customer and mention what areas/types are currently available.
4. Keep the reply concise, professional, and suitable for a WhatsApp message (use bullet points or bold text if necessary). Reply in the same language as the customer's message (Arabic or English).
"""

    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Thank you for reaching out! Our team will get back to you shortly with matching options."


# --- 3. SEND WHATSAPP MESSAGE VIA META GRAPH API ---
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
    response = requests.post(url, json=payload, headers=headers)
    print(f"WhatsApp API Response: {response.status_code}")


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
async def receive_webhook(request: Request):
    payload = await request.json()
    try:
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})

        if "messages" in value:
            message_obj = value["messages"][0]
            sender_phone = message_obj["from"]
            
            # Extract text message body
            if message_obj.get("type") == "text":
                user_text = message_obj["text"]["body"].strip()
                
                # Fetch available rows from Sheets
                inventory = get_available_inventory()
                
                # Generate AI match using Gemini
                reply_text = generate_ai_reply(user_text, inventory)
                
                # Send reply to customer (no lead data stored)
                send_whatsapp_message(sender_phone, reply_text)

    except Exception as e:
        print(f"Error processing webhook: {e}")

    return {"status": "success"}
