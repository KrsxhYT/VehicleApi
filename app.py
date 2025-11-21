from flask import Flask, request, jsonify
import requests, time, re
from bs4 import BeautifulSoup
from flask_cors import CORS   # <-- Added

app = Flask(__name__)
CORS(app)  # <-- Added (Global CORS enable)

# Simple in-memory cache: rc_number -> (timestamp, data)
CACHE = {}
CACHE_TTL = 10 * 60  # 10 minutes

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Linux; Android 10; Mobile) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

def is_cached(rc):
    ent = CACHE.get(rc)
    if not ent:
        return None
    ts, data = ent
    if time.time() - ts < CACHE_TTL:
        return data
    CACHE.pop(rc, None)
    return None

def set_cache(rc, value):
    CACHE[rc] = (time.time(), value)

def normalize_rc(rc: str) -> str:
    return re.sub(r'\s+', '', rc.strip().upper())

def fetch_html(url, headers=None, timeout=10):
    hdrs = HEADERS.copy()
    if headers:
        hdrs.update(headers)
    resp = requests.get(url, headers=hdrs, timeout=timeout)
    resp.raise_for_status()
    return resp.text

def extract_by_label(soup, label):
    try:
        el = soup.find(lambda t: t.name in ("span", "label") and t.get_text(strip=True).strip() == label)
        if el:
            sib = el.find_next_sibling()
            if sib and sib.get_text(strip=True):
                return sib.get_text(strip=True)
            parent = el.find_parent()
            if parent:
                p = parent.find("p")
                if p and p.get_text(strip=True):
                    return p.get_text(strip=True)

        text_node = soup.find(string=lambda s: s and label in s)
        if text_node:
            parent = text_node.find_parent()
            if parent:
                p = parent.find("p")
                if p and p.get_text(strip=True):
                    return p.get_text(strip=True)

        txt = soup.get_text(separator="\n")
        m = re.search(re.escape(label) + r"[:\s\-]*([^\n]{2,200})", txt, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    except Exception:
        return None
    return None

def get_vehicle_details(rc_number: str) -> dict:
    rc = normalize_rc(rc_number)
    cached = is_cached(rc)
    if cached:
        return {"_cached": True, **cached}

    url = f"https://vahanx.in/rc-search/{rc}"
    try:
        html = fetch_html(url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {e}"}
    except Exception as e:
        return {"error": f"Parse error: {e}"}

    labels = [
        "Owner Name", "Father's Name", "Owner Serial No", "Model Name",
        "Maker Model", "Vehicle Class", "Fuel Type", "Fuel Norms",
        "Registration Date", "Insurance Company", "Insurance No",
        "Insurance Expiry", "Insurance Upto", "Fitness Upto", "Tax Upto",
        "PUC No", "PUC Upto", "Financier Name", "Registered RTO",
        "Address", "City Name", "Phone"
    ]

    data = {}
    found_any = False
    for lab in labels:
        val = extract_by_label(soup, lab)
        if val:
            found_any = True
        data[lab] = val

    result = {"found": found_any, "data": data}
    set_cache(rc, result)
    return result

@app.route("/", methods=["GET", "OPTIONS"])  # <-- OPTIONS added
def api_root():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200  # <-- Handles preflight

    rc_number = request.args.get("rc_number")
    if not rc_number:
        return jsonify({
            "credit": "API DEVELOPER: @KrsxhNvrDie",
            "status": "error",
            "message": "Missing required parameter: rc_number"
        }), 400

    details = get_vehicle_details(rc_number)
    if details.get("error"):
        return jsonify({
            "credit": "API DEVELOPER: @KrsxhNvrDie",
            "status": "error",
            "message": details["error"]
        }), 502

    if not details.get("found"):
        return jsonify({
            "credit": "API DEVELOPER: @KrsxhNvrDie",
            "status": "not_found",
            "message": f"No details found for {normalize_rc(rc_number)}"
        }), 404

    return jsonify({
        "credit": "API DEVELOPER: @KrsxhNvrDie",
        "status": "success",
        "rc_number": normalize_rc(rc_number),
        "details": details["data"]
    })
