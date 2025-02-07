from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import base64
import io
from PIL import Image
from geopy.distance import geodesic
import google.generativeai as genai
import json
import re

app = Flask(__name__)
CORS(app)


# Configure MongoDB Atlas Cloud Database
# Replace <db_password> with your actual database password.
#uri = "mongodb+srv://hrshthnaidu:Harshith1234%23@cluster0.0lcuwou.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
uri = "mongodb+srv://hrshthnaidu:harshith@cluster0.xelcz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(uri, server_api=ServerApi('1'))

# Optional: Confirm connection by pinging the deployment
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print("Error connecting to MongoDB:", e)

db = client["zomato_db"]
restaurants_collection = db["restaurants"]

# Configure Google Gemini AI
genai.configure(api_key="AIzaSyBHsg2-HMmjnMwZllrRV9eQDrDYaffMH80")  # Replace with your actual API key

# Get restaurant list with pagination by city
@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    city = request.args.get('city', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 5

    if not city:
        return jsonify({"error": "City parameter is required"}), 400

    query = {"city": city}
    total_count = restaurants_collection.count_documents(query)
    restaurants = list(
        restaurants_collection.find(query, {"_id": 0})
        .skip((page - 1) * per_page)
        .limit(per_page)
    )

    return jsonify({
        "restaurants": restaurants,
        "page": page,
        "total_pages": (total_count + per_page - 1) // per_page
    })

# Get restaurant details by ID
@app.route('/restaurant/<restaurant_id>', methods=['GET'])
def get_restaurant_details(restaurant_id):
    restaurant = restaurants_collection.find_one({"restaurant_id": restaurant_id}, {"_id": 0})
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    return jsonify(restaurant)

# Identify food via image upload
@app.route('/identify-food', methods=['POST'])
def identify_food():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    try:
        image_file = request.files['image']
        image = Image.open(image_file)

        # Compress and encode image
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        prompt = "Return JSON only: {\"identified_cuisine\": \"cuisine_name\"}"

        # Call Google Gemini API
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        response = model.generate_content([
            {"mime_type": "image/jpeg", "data": encoded_image},
            prompt
        ])

        # Debugging: Print full AI response
        print("Raw AI Response:", response)

        if not response or not hasattr(response, "text"):
            return jsonify({"error": "Invalid response from AI"}), 500

        # Extract JSON from AI response (removing ```json ... ```)
        json_text = re.sub(r"```json\n|\n```", "", response.text.strip())

        try:
            cuisine_data = json.loads(json_text)  # Convert to dictionary
            cuisine_name = cuisine_data.get("identified_cuisine", "").strip()
        except json.JSONDecodeError as e:
            return jsonify({"error": "Failed to parse AI response", "details": str(e)}), 500

        if not cuisine_name:
            return jsonify({"error": "No cuisine identified"}), 400

        # Fetch restaurants serving this cuisine
        page = int(request.args.get("page", 1))
        per_page = 5
        query = {"cuisines": {"$regex": cuisine_name, "$options": "i"}}

        total_count = restaurants_collection.count_documents(query)
        restaurants = list(
            restaurants_collection.find(query, {"_id": 0})
            .skip((page - 1) * per_page)
            .limit(per_page)
        )

        return jsonify({
            "identified_cuisine": cuisine_name,
            "restaurants": restaurants,
            "page": page,
            "total_pages": (total_count + per_page - 1) // per_page
        })

    except Exception as e:
        print("Error in /identify-food:", str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# Fetch restaurants by identified cuisine
@app.route('/restaurants-by-cuisine', methods=['GET'])
def get_restaurants_by_cuisine():
    cuisine = request.args.get('cuisine', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 5

    if not cuisine:
        return jsonify({"error": "Cuisine parameter is required"}), 400

    # Use regex to match cuisine as a word in the comma-separated string
    query = {"cuisines": {"$regex": f"\\b{cuisine}\\b", "$options": "i"}}  # Match whole words
    print(query)
    total_count = restaurants_collection.count_documents(query)

    restaurants = list(
        restaurants_collection.find(query, {"_id": 0})
        .skip((page - 1) * per_page)
        .limit(per_page)
    )

    return jsonify({
        "restaurants": restaurants,
        "page": page,
        "total_pages": (total_count + per_page - 1) // per_page
    })

if __name__ == '__main__':
    # Listen on all available interfaces
    app.run(debug=True, host="0.0.0.0")
