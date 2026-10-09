from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any

import requests
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from ai_agent import generate_reply
from sheets_loader import force_refresh, get_cache_status, get_knowledge

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

APP_NAME = os.getenv("APP_NAME", "Medical Lab WhatsApp AI")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "").strip()
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
GRAPH_VERSION = os.getenv("WHATSAPP_GRAPH_VERSION", "v20.0").strip()
APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "").strip()
API_TIMEOUT = float(os.getenv("WHATSAPP_API_TIMEOUT_SECONDS", "15"))

ADMIN_PHONE_NUMBERS = {
    item.strip().lstrip("+").replace(" ", "")
    for item in os.getenv("ADMIN_PHONE_NUMBERS", "").split(",")
    if item.strip()
}

START_TIME = time.time()


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: int


def _validate_configuration() -> None:
    required = {
        "WHATSAPP_VERIFY_TOKEN": VERIFY_TOKEN,
        "WHATSAPP_ACCESS_TOKEN": ACCESS_TOKEN,
        "WHATSAPP_PHONE_NUMBER_ID": PHONE_NUMBER_ID,
        "WHATSAPP_APP_SECRET": APP_SECRET,
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", "").strip(),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    _validate_configuration()
    logger.info("%s starting", APP_NAME)
    yield
    logger.info("%s stopping", APP_NAME)


app = FastAPI(title=APP_NAME, version="1.0.0", lifespan=lifespan)


def _verify_meta_signature(raw_body: bytes, signature_header: str | None) -> bool:
    if not APP_SECRET:
        return False
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    supplied = signature_header.split("=", 1)[1]
    expected = hmac.new(
        APP_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, supplied)


def _graph_messages_url() -> str:
    return (
        f"https://graph.facebook.com/{GRAPH_VERSION}/"
        f"{PHONE_NUMBER_ID}/messages"
    )


def _send_whatsapp_text_sync(recipient: str, message: str) -> None:
    if not ACCESS_TOKEN:
        raise RuntimeError("WHATSAPP_ACCESS_TOKEN is not configured")

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message[:4096],
        },
    }

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = requests.post(
                _graph_messages_url(),
                headers={
                    "Authorization": f"Bearer {ACCESS_TOKEN}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=API_TIMEOUT,
            )

            if response.ok:
                return

            retryable = response.status_code == 429 or response.status_code >= 500
            if not retryable:
                logger.error(
                    "WhatsApp API rejected message: status=%s body=%s",
                    response.status_code,
                    response.text[:1000],
                )
                response.raise_for_status()

            logger.warning(
                "Transient WhatsApp API failure on attempt %d: status=%s",
                attempt + 1,
                response.status_code,
            )
            if attempt < 2:
                time.sleep(2 ** attempt)
        except requests.RequestException as exc:
            last_error = exc
            logger.warning(
                "WhatsApp API request failed on attempt %d: %s",
                attempt + 1,
                exc,
            )
            if attempt < 2:
                time.sleep(2 ** attempt)

    if last_error:
        raise last_error

    response.raise_for_status()


async def send_whatsapp_text(recipient: str, message: str) -> None:
    await asyncio.to_thread(_send_whatsapp_text_sync, recipient, message)


def _admin_status_message() -> str:
    try:
        get_knowledge(force_refresh=False)
    except Exception:
        logger.exception("Unable to initialize knowledge for admin status")

    status = get_cache_status()
    age = status["age_seconds"]
    age_text = "not loaded" if age is None else f"{age:.0f}s ago"

    if status["source"] == "google_sheets":
        connectivity = "Google Sheets: connected"
    elif status["source"] == "fallback":
        connectivity = "Google Sheets: unavailable; using local fallback"
    else:
        connectivity = "Google Sheets: not loaded"

    return (
        f"Server: online\n"
        f"Uptime: {int(time.time() - START_TIME)}s\n"
        f"Cache: {status['source'] or 'empty'} ({age_text})\n"
        f"TTL: {status['ttl_seconds']}s\n"
        f"Tests cached: {status['test_count']}\n"
        f"{connectivity}"
    )


def _admin_refresh_message() -> str:
    snapshot = force_refresh()
    timestamp = time.strftime(
        "%Y-%m-%d %H:%M:%S UTC",
        time.gmtime(snapshot.loaded_at),
    )

    if snapshot.source == "google_sheets":
        source_line = "Google Sheets loaded successfully."
    else:
        source_line = (
            "Google Sheets failed; local fallback was loaded. "
            f"Error: {snapshot.sheet_error or 'unknown'}"
        )

    clinic_name = snapshot.info.get("lab_name", "Unknown clinic")

    return (
        "Refresh complete.\n"
        f"Clinic: {clinic_name}\n"
        f"Tests loaded: {snapshot.test_count}\n"
        f"Source: {snapshot.source}\n"
        f"Timestamp: {timestamp}\n"
        f"{source_line}"
    )


def _normalize_phone(value: str) -> str:
    return value.strip().lstrip("+").replace(" ", "").replace("-", "")


def _is_admin(phone: str) -> bool:
    return _normalize_phone(phone) in ADMIN_PHONE_NUMBERS


def _extract_text_messages(payload: dict[str, Any]) -> list[tuple[str, str]]:
    messages: list[tuple[str, str]] = []

    for entry in payload.get("entry", []):
        if not isinstance(entry, dict):
            continue

        for change in entry.get("changes", []):
            if not isinstance(change, dict):
                continue

            value = change.get("value", {})
            if not isinstance(value, dict):
                continue

            for message in value.get("messages", []):
                if not isinstance(message, dict):
                    continue

                if message.get("type") != "text":
                    continue

                sender = str(message.get("from", "")).strip()
                body = (
                    message.get("text", {}).get("body", "")
                    if isinstance(message.get("text"), dict)
                    else ""
                )

                if sender and body:
                    messages.append((sender, str(body).strip()))

    return messages


async def _process_incoming_message(sender: str, text: str) -> None:
    normalized_command = text.strip().lower()

    try:
        if _is_admin(sender):
            if normalized_command in {"/refresh", "تحديث", "ريفرش"}:
                reply = await asyncio.to_thread(_admin_refresh_message)
                await send_whatsapp_text(sender, reply)
                return

            if normalized_command in {"/status", "الحالة"}:
                reply = await asyncio.to_thread(_admin_status_message)
                await send_whatsapp_text(sender, reply)
                return

        reply = await generate_reply(text)
        await send_whatsapp_text(sender, reply)

    except Exception:
        logger.exception("Failed to process incoming message from %s", sender)
        try:
            await send_whatsapp_text(
                sender,
                "عذراً، حدث خطأ مؤقت. يرجى المحاولة مرة أخرى لاحقاً.",
            )
        except Exception:
            logger.exception("Failed to send error response to %s", sender)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        uptime_seconds=int(time.time() - START_TIME),
    )


@app.get("/webhook/whatsapp", response_class=PlainTextResponse)
async def verify_whatsapp_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> str:
    if (
        hub_mode == "subscribe"
        and hub_verify_token
        and hmac.compare_digest(hub_verify_token, VERIFY_TOKEN)
        and hub_challenge is not None
    ):
        return hub_challenge

    raise HTTPException(status_code=403, detail="Webhook verification failed")


@app.post("/webhook/whatsapp")
async def receive_whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
) -> dict[str, bool]:
    raw_body = await request.body()

    if not _verify_meta_signature(raw_body, x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    for sender, text in _extract_text_messages(payload):
        background_tasks.add_task(_process_incoming_message, sender, text)

    return {"ok": True}
