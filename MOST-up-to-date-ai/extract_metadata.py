import os
import re
import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_path
from dateutil.parser import parse as parse_date

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ───────────────────────────────────────────────────────────────────────────
# 1) CONFIGURATION & SETUP
# ───────────────────────────────────────────────────────────────────────────
BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
PDF_ROOT_FOLDER  = os.path.join(BASE_DIR, "scanned_pdfs")
CRED_FOLDER      = os.path.join(BASE_DIR, "credentials")
SERVICE_KEY      = os.path.join(CRED_FOLDER, "service_account_key.json")
SPREADSHEET_ID   = os.getenv("GOOGLE_SHEET_ID", "1ipTfzA5qK8V7BvzuO-hiFCbG50qjhcQP_igndLquEj8")

# ───────────────────────────────────────────────────────────────────────────
# 2) HELPER FUNCTIONS
# ───────────────────────────────────────────────────────────────────────────
def preprocess_page(pil_page):
    img    = cv2.cvtColor(np.array(pil_page), cv2.COLOR_RGB2BGR)
    gray   = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binar  = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, blockSize=51, C=10)

    # deskew
    coords = np.column_stack(np.where(binar > 0))
    angle  = cv2.minAreaRect(coords)[-1]
    if angle < -45: angle += 90
    elif angle > 45: angle -= 90

    (h, w)  = binar.shape
    M       = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
    deskew  = cv2.warpAffine(binar, M, (w, h),
                             flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REPLICATE)
    return deskew


def ocr_pdf(pdf_path):
    """
    OCR PDF → full_text + average confidence%.
    Fix: handle both str & int confidences from pytesseract.
    """
    pages, full_text, confs = convert_from_path(pdf_path, dpi=300), "", []
    for pil_page in pages:
        img = preprocess_page(pil_page)

        # run tesseract
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        txt  = pytesseract.image_to_string(img, lang="eng")
        full_text += txt + "\n\n"

        # collect per-word confidences, guard both str and int
        word_confs = []
        for c in data.get("conf", []):
            try:
                ci = int(c)
                if ci >= 0:
                    word_confs.append(ci)
            except (ValueError, TypeError):
                continue

        confs.append(sum(word_confs)/len(word_confs) if word_confs else 0)

    avg_conf = sum(confs)/len(confs) if confs else 0
    return full_text, avg_conf


def regex_date(text):
    """Try a simple dd/mm/yyyy or yyyy; fallback to UNKNOWN."""
    m = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4})\b", text)
    if m:
        try:
            return parse_date(m.group(), dayfirst=True).strftime("%Y/%m/%d")
        except:
            return m.group()
    return "UNKNOWN"


def simple_metadata(full_text):
    """First nonempty line as Title, first 100 chars as desc, date via regex."""
    lines = [l.strip() for l in full_text.splitlines() if l.strip()]
    title = lines[0] if lines else "UNKNOWN"
    desc  = (full_text.replace("\n"," ")[:100].strip() or "UNKNOWN")
    date  = regex_date(full_text)
    return {"Title": title, "Description": desc, "Date": date}


# ───────────────────────────────────────────────────────────────────────────
# 3) GOOGLE SHEETS FUNCTIONS
# ───────────────────────────────────────────────────────────────────────────
def fetch_all_tab_names():
    creds   = Credentials.from_service_account_file(SERVICE_KEY,
               scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    svc     = build("sheets", "v4", credentials=creds)
    sheet   = svc.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    return [s["properties"]["title"] for s in sheet.get("sheets", [])]


def append_rows_to_tab(tab_name, rows):
    creds = Credentials.from_service_account_file(
        SERVICE_KEY,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    svc = build("sheets", "v4", credentials=creds).spreadsheets()

    # you said your Document1 lives in row 3,
    # so we'll start writing at C3 and go down len(rows) rows
    start_row = 3
    end_row   = start_row + len(rows) - 1
    write_range = f"'{tab_name}'!C{start_row}:G{end_row}"
    print(f"[DEBUG] Writing into {write_range}")

    body = {
        "valueInputOption": "RAW",
        "data": [{
            "range": write_range,
            "majorDimension": "ROWS",
            "values": rows
        }]
    }

    svc.values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=body
    ).execute()



# ───────────────────────────────────────────────────────────────────────────
# 4) MAIN PIPELINE
# ───────────────────────────────────────────────────────────────────────────
def main():
    tabs = fetch_all_tab_names()
    print("Detected tabs:")
    for t in tabs: print(" •", t)

    os.makedirs(PDF_ROOT_FOLDER, exist_ok=True)
    for t in tabs:
        d = os.path.join(PDF_ROOT_FOLDER, t)
        if not os.path.isdir(d):
            print(f"🔨 creating folder for {t!r}")
            os.makedirs(d, exist_ok=True)

    # map only existing folders
    folders = {f: f for f in os.listdir(PDF_ROOT_FOLDER)
               if os.path.isdir(os.path.join(PDF_ROOT_FOLDER, f)) and f in tabs}
    if not folders:
        print("⚠️ no matching folders → exiting")
        return

    for fld, tab in folders.items():
        path = os.path.join(PDF_ROOT_FOLDER, fld)
        print(f"\n▶ Processing '{fld}' → '{tab}'")
        rows = []
        for fn in os.listdir(path):
            if not fn.lower().endswith(".pdf"):
                continue
            pdf_path = os.path.join(path, fn)
            print("   • OCR:", fn)
            text, conf = ocr_pdf(pdf_path)
            meta       = simple_metadata(text)
            rows.append([fn,
                         meta["Title"],
                         meta["Description"],
                         meta["Date"],
                         f"{conf:.1f}%"])
        if rows:
            print(f"  ➜ appending {len(rows)} rows")
            append_rows_to_tab(tab, rows)
        else:
            print(f"  ⚠️ no PDFs in '{fld}', skipping")
    print("\n🏁 done.")

if __name__ == "__main__":
    main()
