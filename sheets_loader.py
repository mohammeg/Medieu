from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv()

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


@dataclass(frozen=True)
class KnowledgeSnapshot:
    tests: list[dict[str, Any]]
    info: dict[str, str]
    source: str
    loaded_at: float
    sheet_error: str | None = None

    @property
    def test_count(self) -> int:
        return len(self.tests)


_cache_lock = threading.RLock()
_cached_snapshot: KnowledgeSnapshot | None = None


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _fallback_path() -> Path:
    return Path(os.getenv("LAB_DATA_FILE", "lab_data.json"))


def _read_fallback() -> KnowledgeSnapshot:
    path = _fallback_path()
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    tests = payload.get("tests", [])
    info = payload.get("info", {})

    if not isinstance(tests, list) or not isinstance(info, dict):
        raise ValueError("lab_data.json must contain 'tests' as a list and 'info' as an object")

    normalized_tests: list[dict[str, Any]] = []
    for item in tests:
        if not isinstance(item, dict):
            continue
        normalized_tests.append(
            {
                "test_key": str(item.get("test_key", "")).strip(),
                "name": str(item.get("name", "")).strip(),
                "name_ar": str(item.get("name_ar", "")).strip(),
                "price": str(item.get("price", "")).strip(),
                "fasting_hours": item.get("fasting_hours", 0),
                "notes": str(item.get("notes", "")).strip(),
            }
        )

    return KnowledgeSnapshot(
        tests=normalized_tests,
        info={str(k): str(v) for k, v in info.items()},
        source="fallback",
        loaded_at=time.time(),
        sheet_error=None,
    )


def _service_account_credentials() -> Credentials:
    credentials_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if credentials_json:
        try:
            info = json.loads(credentials_json)
        except json.JSONDecodeError as exc:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON") from exc
        return Credentials.from_service_account_info(info, scopes=SCOPES)

    credentials_path = Path(
        os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
    )
    if not credentials_path.exists():
        raise FileNotFoundError(
            f"Google service-account file not found: {credentials_path}"
        )
    return Credentials.from_service_account_file(str(credentials_path), scopes=SCOPES)


def _required_headers(headers: list[str], required: set[str], worksheet: str) -> None:
    normalized = {str(h).strip() for h in headers}
    missing = required - normalized
    if missing:
        raise ValueError(
            f"Worksheet '{worksheet}' is missing required columns: {', '.join(sorted(missing))}"
        )


def _load_from_sheets() -> KnowledgeSnapshot:
    spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID", "").strip()
    if not spreadsheet_id:
        raise ValueError("GOOGLE_SPREADSHEET_ID is not configured")

    tests_worksheet = os.getenv("TESTS_WORKSHEET", "Tests")
    info_worksheet = os.getenv("INFO_WORKSHEET", "Info")

    credentials = _service_account_credentials()
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(spreadsheet_id)

    tests_ws = spreadsheet.worksheet(tests_worksheet)
    info_ws = spreadsheet.worksheet(info_worksheet)

    test_rows = tests_ws.get_all_records()
    info_rows = info_ws.get_all_records()

    tests: list[dict[str, Any]] = []
    for row in test_rows:
        tests.append(
            {
                "test_key": str(row.get("Test_Key", "")).strip(),
                "name": str(row.get("Name", "")).strip(),
                "name_ar": "",
                "price": str(row.get("Price", "")).strip(),
                "fasting_hours": row.get("Fasting_Hours", 0),
                "notes": str(row.get("Notes", "")).strip(),
            }
        )

    info: dict[str, str] = {}
    for row in info_rows:
        key = str(row.get("Key", "")).strip()
        value = str(row.get("Value", "")).strip()
        if key:
            info[key] = value

    if not tests:
        logger.warning("Google Sheet Tests worksheet returned zero rows")
    if not info:
        logger.warning("Google Sheet Info worksheet returned zero rows")

    return KnowledgeSnapshot(
        tests=tests,
        info=info,
        source="google_sheets",
        loaded_at=time.time(),
        sheet_error=None,
    )


def load_knowledge(force_refresh: bool = False) -> KnowledgeSnapshot:
    global _cached_snapshot

    ttl = max(1, _env_int("SHEETS_CACHE_TTL_SECONDS", 600))
    now = time.time()

    with _cache_lock:
        if (
            not force_refresh
            and _cached_snapshot is not None
            and now - _cached_snapshot.loaded_at < ttl
        ):
            return _cached_snapshot

        try:
            snapshot = _load_from_sheets()
            _cached_snapshot = snapshot
            logger.info(
                "Knowledge loaded from Google Sheets: %d tests",
                snapshot.test_count,
            )
            return snapshot
        except Exception as exc:
            logger.exception("Google Sheets load failed; using local fallback")

            try:
                fallback = _read_fallback()
            except Exception:
                logger.exception("Local fallback also failed")
                if _cached_snapshot is not None:
                    return _cached_snapshot
                raise

            fallback = KnowledgeSnapshot(
                tests=fallback.tests,
                info=fallback.info,
                source="fallback",
                loaded_at=now,
                sheet_error=str(exc),
            )
            _cached_snapshot = fallback
            return fallback


def force_refresh() -> KnowledgeSnapshot:
    return load_knowledge(force_refresh=True)


def get_cache_status() -> dict[str, Any]:
    ttl = max(1, _env_int("SHEETS_CACHE_TTL_SECONDS", 600))
    with _cache_lock:
        snapshot = _cached_snapshot

    if snapshot is None:
        return {
            "loaded": False,
            "source": None,
            "age_seconds": None,
            "ttl_seconds": ttl,
            "expired": True,
            "test_count": 0,
            "sheet_error": None,
        }

    age = max(0.0, time.time() - snapshot.loaded_at)
    return {
        "loaded": True,
        "source": snapshot.source,
        "age_seconds": round(age, 1),
        "ttl_seconds": ttl,
        "expired": age >= ttl,
        "test_count": snapshot.test_count,
        "sheet_error": snapshot.sheet_error,
        "loaded_at": snapshot.loaded_at,
    }


def get_knowledge(force_refresh: bool = False) -> KnowledgeSnapshot:
    return load_knowledge(force_refresh=force_refresh)
