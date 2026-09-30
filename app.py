import os
import json
import base64
import re
from urllib.parse import quote_plus

from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=None)

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

client = None
if GEMINI_API_KEY and genai:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception:
        client = None


def money(value):
    try:
        return f"₹{float(value):,.0f}"
    except (TypeError, ValueError):
        return "₹0"


def search_url(platform, query):
    domains = {
        "Amazon": "amazon.in",
        "Flipkart": "flipkart.com",
        "IKEA": "ikea.com/in/en",
        "Swiggy": "swiggy.com",
        "Zomato": "zomato.com",
        "OYO": "oyorooms.com",
    }
    domain = domains.get(platform, "")
    if platform == "IKEA":
        return f"https://www.ikea.com/in/en/search/?q={quote_plus(query)}"
    if platform == "Swiggy":
        return f"https://www.swiggy.com/search?query={quote_plus(query)}"
    if platform == "Zomato":
        return f"https://www.zomato.com/search?query={quote_plus(query)}"
    if platform == "OYO":
        return f"https://www.oyorooms.com/search?location={quote_plus(query)}"
    if domain:
        return f"https://www.google.com/search?q=site%3A{quote_plus(domain)}+{quote_plus(query)}"
    return f"https://www.google.com/search?q={quote_plus(query)}"


def clean_json(text):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def fallback_plan(planner, data):
    budget = float(data.get("budget", 0) or 0)
    style = data.get("style", "modern")
    if planner == "home":
        rooms = data.get("rooms", "Living Room")
        items = [
            ("LED Ceiling Light", "Amazon", max(700, budget * .08), "Energy-efficient lighting"),
            ("Compact Side Table", "IKEA", max(1200, budget * .15), f"{style.title()} space-friendly furniture"),
            ("Decorative Wall Art", "Flipkart", max(500, budget * .07), "Low-cost visual upgrade"),
            ("Cushion Set", "Amazon", max(600, budget * .08), "Adds color and comfort"),
            ("Indoor Plant / Planter", "IKEA", max(500, budget * .06), "Simple natural accent"),
        ]
        categories = [
            {"category": "Lighting", "allocation": round(budget*.20), "reason": "Improve function and ambience."},
            {"category": "Furniture", "allocation": round(budget*.40), "reason": "Prioritize essential pieces."},
            {"category": "Decor", "allocation": round(budget*.25), "reason": "Use affordable visual accents."},
            {"category": "Buffer", "allocation": round(budget*.15), "reason": "Keep a reserve for delivery or changes."},
        ]
        return make_response("Home Interior", budget, categories, items, f"Plan for {rooms} with a {style} style.")
    if planner == "party":
        guests = int(data.get("guests", 10) or 10)
        event = data.get("event_type", "Birthday")
        items = [
            ("Food / Catering Package", "Swiggy", budget*.38, f"Food plan for about {guests} guests"),
            ("Venue Search", "OYO", budget*.20, "Compare suitable venues or stays"),
            ("Decor Package", "Amazon", budget*.15, f"{event} decoration essentials"),
            ("Cake / Dessert", "Zomato", budget*.12, "Compare nearby dessert options"),
            ("Entertainment / Extras", "Amazon", budget*.10, "Keep activities within the reserve"),
        ]
        categories = [
            {"category": "Food", "allocation": round(budget*.38), "reason": "Largest share for guests."},
            {"category": "Venue", "allocation": round(budget*.20), "reason": "Control location and capacity cost."},
            {"category": "Decoration", "allocation": round(budget*.15), "reason": "Create the event atmosphere."},
            {"category": "Dessert", "allocation": round(budget*.12), "reason": "Set aside a predictable food add-on."},
            {"category": "Reserve", "allocation": round(budget*.15), "reason": "Handle last-minute expenses."},
        ]
        return make_response("Party Planner", budget, categories, items, f"{event} plan for {guests} guests.")
    items = [
        ("Minimal Pendant Necklace", "Amazon", budget*.28, "Versatile for the selected occasion"),
        ("Stud / Drop Earrings", "Flipkart", budget*.18, "Easy matching accessory"),
        ("Bracelet", "Amazon", budget*.15, "Adds a coordinated accent"),
        ("Statement Earrings", "Flipkart", budget*.22, "Alternative if a bolder look is desired"),
        ("Simple Ring", "Amazon", budget*.10, "Optional finishing piece"),
    ]
    categories = [
        {"category": "Primary Jewelry", "allocation": round(budget*.45), "reason": "Choose one main focal piece."},
        {"category": "Earrings", "allocation": round(budget*.22), "reason": "Coordinate with the outfit."},
        {"category": "Accessories", "allocation": round(budget*.18), "reason": "Add subtle supporting pieces."},
        {"category": "Reserve", "allocation": round(budget*.15), "reason": "Keep flexibility for final selection."},
    ]
    return make_response("Jewelry Planner", budget, categories, items, "A coordinated jewelry set based on the stated occasion and style.")


def make_response(title, budget, categories, items, summary):
    recs = []
    for name, platform, price, reason in items:
        query = f"{name} {reason}"
        recs.append({
            "name": name,
            "platform": platform,
            "estimated_price": round(float(price)),
            "reason": reason,
            "search_url": search_url(platform, query),
        })
    return {
        "title": title,
        "summary": summary,
        "budget": budget,
        "estimated_total": round(sum(x["estimated_price"] for x in recs)),
        "budget_categories": categories,
        "recommendations": recs,
        "source": "Demo fallback",
        "disclaimer": "Prices and availability are estimates. Open a platform link to verify the current listing."
    }


def build_prompt(planner, data):
    schema = """Return ONLY valid JSON with this shape:
{
  "title": "string",
  "summary": "string",
  "budget": number,
  "estimated_total": number,
  "budget_categories": [{"category":"string","allocation":number,"reason":"string"}],
  "recommendations": [
    {"name":"string","platform":"Amazon|Flipkart|IKEA|Swiggy|Zomato|OYO","estimated_price":number,"reason":"string"}
  ],
  "disclaimer":"string"
}
Use INR. Keep estimated_total <= budget whenever practical. Do not claim live prices, inventory, reviews, or availability. Recommendations may be search-oriented rather than verified listings."""
    context = json.dumps(data, ensure_ascii=False)
    return f"""You are PocketSmart AI, a budget planning assistant.
Planner: {planner}
User input: {context}
Create 5 to 8 practical recommendations and a sensible category-wise budget allocation.
For platforms, select only from Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO.
If a platform is not naturally relevant, use Amazon or Flipkart for physical products.
{schema}"""


def call_gemini(planner, data, image_bytes=None, image_mime=None):
    if not client:
        return None
    prompt = build_prompt(planner, data)
    contents = [prompt]
    if image_bytes and types:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime or "image/jpeg"))
        contents.append("The uploaded image is an outfit reference. Use only visible, non-sensitive style/color information.")
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            temperature=0.4,
            response_mime_type="application/json",
        ),
    )
    raw = clean_json(response.text)
    return json.loads(raw)


def normalize_result(result):
    result["budget"] = float(result.get("budget", 0) or 0)
    result["estimated_total"] = float(result.get("estimated_total", 0) or 0)
    for rec in result.get("recommendations", []):
        rec["estimated_price"] = float(rec.get("estimated_price", 0) or 0)
        rec.setdefault("platform", "Amazon")
        rec.setdefault("reason", "Budget-friendly option")
        rec["search_url"] = search_url(rec["platform"], rec.get("name", "product"))
    result.setdefault("budget_categories", [])
    result.setdefault("recommendations", [])
    result.setdefault("disclaimer", "Prices and availability are estimates; verify them on the destination platform.")
    return result


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/style.css")
def css():
    return send_from_directory(BASE_DIR, "style.css", mimetype="text/css")


@app.get("/script.js")
def js():
    return send_from_directory(BASE_DIR, "script.js", mimetype="application/javascript")


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "ai_configured": bool(client),
        "model": GEMINI_MODEL,
        "message": "PocketSmart AI is running."
    })


@app.post("/api/recommend")
def recommend():
    try:
        planner = request.form.get("planner", "home").strip().lower()
        if planner not in {"home", "party", "jewelry"}:
            return jsonify({"error": "Invalid planner."}), 400

        budget_raw = request.form.get("budget", "0")
        budget = float(budget_raw)
        if budget <= 0:
            return jsonify({"error": "Please enter a budget greater than zero."}), 400

        data = dict(request.form)
        data["budget"] = budget

        image_bytes = None
        image_mime = None
        if "outfit_image" in request.files:
            image = request.files["outfit_image"]
            if image and image.filename:
                image_bytes = image.read()
                image_mime = image.mimetype
                if len(image_bytes) > 5 * 1024 * 1024:
                    return jsonify({"error": "Image must be 5 MB or smaller."}), 400

        try:
            result = call_gemini(planner, data, image_bytes, image_mime)
            if result:
                result = normalize_result(result)
                result["source"] = f"Gemini ({GEMINI_MODEL})"
                return jsonify(result)
        except Exception as ai_error:
            app.logger.warning("Gemini unavailable: %s", ai_error)

        return jsonify(fallback_plan(planner, data))

    except ValueError:
        return jsonify({"error": "Budget and numeric fields must contain valid numbers."}), 400
    except Exception:
        app.logger.exception("Recommendation request failed")
        return jsonify({"error": "Something went wrong while creating the plan."}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "0") == "1")
