from flask import Flask, request, jsonify
import google.generativeai as genai
import base64
import io
import PIL.Image

# Initialize Flask app
app = Flask(__name__)

# Set up Google Generative AI API
genai.configure(api_key="YOUR_GOOGLE_API_KEY")

# Define the model
model = genai.GenerativeModel(model_name="gemini-1.5-pro")

@app.route('/predict_food', methods=['POST'])
def predict_food():
    # Check if the request contains an image
    if 'image' not in request.files:
        return jsonify({"error": "No image found"}), 400

    # Get the image from the request
    image_file = request.files['image']
    
    # Load and compress the image
    image = PIL.Image.open(image_file)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    image_bytes = buffer.getvalue()

    # Create a prompt
    prompt = "Just give the name of the food present in the image, don't give anything else in form of a json"
    
    # Generate response from Gemini
    response = model.generate_content(
        [
            {
                "mime_type": "image/jpeg", 
                "data": base64.b64encode(image_bytes).decode("utf-8"),
            },
            prompt,
        ]
    )
    
    # Extract and send back the response
    food_name = response.text.strip()  # Ensure no unwanted spaces or characters
    return jsonify({"food_name": food_name})

if __name__ == "__main__":
    # Run the Flask app
    app.run(debug=True, host="0.0.0.0", port=5000)
