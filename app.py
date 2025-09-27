import os
import json
import re
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv

# Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__, 
    template_folder='templates',
    static_folder='static'
)

def fix_json_response(raw_text):
    """Fix common JSON formatting issues in AI response"""
    try:
        # Remove any text before the first { and after the last }
        start_idx = raw_text.find('{')
        end_idx = raw_text.rfind('}') + 1
        if start_idx != -1 and end_idx != -1:
            raw_text = raw_text[start_idx:end_idx]
        
        # Fix common JSON issues
        raw_text = re.sub(r',\s*}', '}', raw_text)
        raw_text = re.sub(r',\s*]', ']', raw_text)
        raw_text = re.sub(r'(\w+):', r'"\1":', raw_text)
        raw_text = re.sub(r':\s*\'([^\']+)\'', r': "\1"', raw_text)
        raw_text = re.sub(r'\\"', '"', raw_text)
        
        return raw_text
    except Exception as e:
        print(f"Error fixing JSON: {e}")
        return raw_text

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    try:
        dest = request.form["destination"]
        days = int(request.form["days"])
        budget = request.form["budget"]
        prefs = request.form.get("preferences", "")
        
        # Get individual preference checkboxes
        preferences_list = []
        for pref in ['adventure', 'culture', 'food', 'relaxation']:
            if request.form.get(f"pref_{pref}"):
                preferences_list.append(pref)
        
        final_prefs = prefs if prefs else ", ".join(preferences_list)

        # Build prompt for OpenAI with Indian Rupees
        prompt = f"""
        Create a detailed travel itinerary in VALID JSON format for an Indian traveler. Follow this EXACT structure:

        {{
          "destination": "{dest}",
          "days": {days},
          "budget": "₹{budget}",
          "preferences": "{final_prefs}",
          "itinerary": [
            {{
              "day": 1,
              "morning": "Activity Title + Detailed description of the activity",
              "afternoon": "Activity Title + Detailed description of the activity", 
              "evening": "Activity Title + Detailed description of the activity",
              "estimated_cost": 2500
            }}
          ],
          "estimated_total_cost": 15000
        }}

        Important rules:
        1. Return ONLY valid JSON, no additional text
        2. All keys must be in double quotes
        3. All string values must be in double quotes
        4. No trailing commas
        5. Ensure all brackets and braces are properly closed
        6. Use INDIAN RUPEES (₹) for all costs, not dollars or euros
        7. Provide realistic cost estimates for Indian travelers
        8. Consider local prices and reasonable expenses
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )

        raw_response = response.choices[0].message.content.strip()
        print("Raw AI Response:", raw_response)
        
        # Try to parse directly first
        try:
            itinerary = json.loads(raw_response)
        except json.JSONDecodeError:
            # If direct parsing fails, try to fix the JSON
            fixed_json = fix_json_response(raw_response)
            itinerary = json.loads(fixed_json)
            
    except Exception as e:
        print(f"Error: {e}")
        return render_template("error.html", 
                             error=str(e), 
                             raw_response=raw_response if 'raw_response' in locals() else 'No response')
    
    return render_template("itinerary.html", itinerary=itinerary)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)