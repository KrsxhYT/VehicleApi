from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# ------------------- #
# VEHICLE INFO FETCHER#
# ------------------- #
def get_vehicle_details(rc_number: str) -> dict:
    rc = rc_number.strip().upper()
    url = f"https://vahanx.in/rc-search/{rc}"

    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }

    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {str(e)}"}

    error_block = soup.find("div", class_="error") or soup.find("div", class_="alert")
    if error_block and "not found" in error_block.get_text(strip=True).lower():
        return {"error": "Vehicle not found or invalid RC number"}

    extracted = {}

    for div in soup.find_all("div"):
        label = div.find("span") or div.find("strong")
        value = div.find("p") or div.find("span", class_="value")

        if label and value:
            key = label.get_text(strip=True)
            val = value.get_text(strip=True)
            if key and val:
                extracted[key] = val

    data = {
        "Owner Name": extracted.get("Owner Name"),
        "Father's Name": extracted.get("Father's Name"),
        "Owner Serial No": extracted.get("Owner Serial No"),
        "Model Name": extracted.get("Model Name"),
        "Maker Model": extracted.get("Maker Model"),
        "Vehicle Class": extracted.get("Vehicle Class"),
        "Fuel Type": extracted.get("Fuel Type"),
        "Fuel Norms": extracted.get("Fuel Norms"),
        "Registration Date": extracted.get("Registration Date"),
        "Insurance Company": extracted.get("Insurance Company"),
        "Insurance No": extracted.get("Insurance No"),
        "Insurance Upto": extracted.get("Insurance Upto"),
        "Fitness Upto": extracted.get("Fitness Upto"),
        "Tax Upto": extracted.get("Tax Upto"),
        "PUC No": extracted.get("PUC No"),
        "PUC Upto": extracted.get("PUC Upto"),
        "Financier Name": extracted.get("Financier Name"),
        "Registered RTO": extracted.get("Registered RTO"),
        "Address": extracted.get("Address"),
        "City Name": extracted.get("City Name"),
        "Phone": extracted.get("Phone"),
    }

    return {k: v for k, v in data.items() if v}

# ------------------- #
# ROOT = GET + POST   #
# ------------------- #
@app.route("/", methods=["GET", "POST"])
def root():
    if request.method == "POST":
        body = request.get_json(silent=True) or request.form
        rc_number = body.get("rc_number")
    else:
        rc_number = request.args.get("rc_number")

    if not rc_number:
        return jsonify({
            "service": "Vehicle RC Details API",
            "usage": {
                "GET": "/?rc_number=DL01AB1234",
                "POST": "/  { rc_number }"
            },
            "status": "online"
        })

    if len(rc_number.strip()) < 3:
        return jsonify({
            "credit": "API DEVELOPER: @J4TNX",
            "status": "error",
            "message": "Invalid or missing rc_number"
        }), 400

    details = get_vehicle_details(rc_number)

    if details.get("error"):
        return jsonify({
            "credit": "API DEVELOPER: @J4TNX",
            "status": "error",
            "message": details["error"]
        }), 500

    if not details:
        return jsonify({
            "credit": "API DEVELOPER: @J4TNX",
            "status": "not_found",
            "message": f"No details found for {rc_number}"
        }), 404

    return jsonify({
        "credit": "API DEVELOPER: @J4TNX",
        "status": "success",
        "rc_number": rc_number.strip().upper(),
        "details": details
    })

# ------------------- #
# HEALTH CHECK        #
# ------------------- #
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Vehicle RC Details API",
        "version": "1.0"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
