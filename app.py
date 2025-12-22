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

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {str(e)}"}

    def get_value(label):
        try:
            label_el = soup.find("span", string=label) or soup.find("strong", string=label)
            if not label_el:
                return None
            parent = label_el.find_parent("div")
            if not parent:
                return None
            val = parent.find("p") or parent.find("span", class_="value")
            return val.get_text(strip=True) if val else None
        except Exception:
            return None

    error_block = soup.find("div", class_="error") or soup.find("div", class_="alert")
    if error_block and "not found" in error_block.get_text(strip=True).lower():
        return {"error": "Vehicle not found or invalid RC number"}

    data = {
        "Owner Name": get_value("Owner Name"),
        "Father's Name": get_value("Father's Name"),
        "Owner Serial No": get_value("Owner Serial No"),
        "Model Name": get_value("Model Name"),
        "Maker Model": get_value("Maker Model"),
        "Vehicle Class": get_value("Vehicle Class"),
        "Fuel Type": get_value("Fuel Type"),
        "Fuel Norms": get_value("Fuel Norms"),
        "Registration Date": get_value("Registration Date"),
        "Insurance Company": get_value("Insurance Company"),
        "Insurance No": get_value("Insurance No"),
        "Insurance Upto": get_value("Insurance Upto"),
        "Fitness Upto": get_value("Fitness Upto"),
        "Tax Upto": get_value("Tax Upto"),
        "PUC No": get_value("PUC No"),
        "PUC Upto": get_value("PUC Upto"),
        "Financier Name": get_value("Financier Name"),
        "Registered RTO": get_value("Registered RTO"),
        "Address": get_value("Address"),
        "City Name": get_value("City Name"),
        "Phone": get_value("Phone"),
    }

    return {k: v for k, v in data.items() if v}

# ------------------- #
# MAIN API "/"        #
# GET + POST JSON     #
# ------------------- #
@app.route("/", methods=["GET", "POST"])
def main_api():
    if request.method == "POST":
        body = request.get_json(silent=True) or request.form
        rc_number = body.get("rc_number")
    else:
        rc_number = request.args.get("rc_number")

    if not rc_number or len(rc_number.strip()) < 3:
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
