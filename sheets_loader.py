import time
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CREDS_FILE = "service_account.json"
SHEET_NAME = "Lab_Data"  # اسم الشيت أو الرابط الكامل

_cached_data = None
_last_fetch = 0
CACHE_TTL = 600  # مدة التخزين المؤقت: 10 دقائق (بالثواني)

def _read_from_sheets():
    """الاتصال الفعلي بجوجل شيتس وقراءة البيانات"""
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME)

    # 1. قراءة الفحوصات
    tests_sheet = sheet.worksheet("Tests")
    tests = tests_sheet.get_all_records()

    # 2. قراءة معلومات المختبر
    info_sheet = sheet.worksheet("Info")
    info_records = info_sheet.get_all_records()
    info = {row["Key"]: row["Value"] for row in info_records if row.get("Key")}

    return {
        "info": info,
        "tests": tests
    }

def get_lab_data(force_refresh: bool = False):
    """
    جلب البيانات مع ميزة الـ Caching.
    إذا كانت force_refresh=True، يتم تجاهل الوقت والقراءة فوراً.
    """
    global _cached_data, _last_fetch
    now = time.time()

    if force_refresh or _cached_data is None or (now - _last_fetch > CACHE_TTL):
        try:
            _cached_data = _read_from_sheets()
            _last_fetch = now
        except Exception as e:
            # في حال وجود انقطاع مؤقت، الاستمرار بالبيانات المحفوظة سابقاً إن وجدت
            if _cached_data is None:
                raise e
    return _cached_data