from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import requests
from PIL import Image
import io
import base64
from food_recognition import FoodRecognizer, get_recipe

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# Initialize the food recognizer
food_recognizer = FoodRecognizer()

# Get API keys from .env file
VISION_API_KEY = os.getenv('VISION_API_KEY')
SPOONACULAR_API_KEY = os.getenv('SPOONACULAR_API_KEY')

# Validate and test API keys on startup
def validate_api_key():
    """Validate the Spoonacular API key on startup"""
    if not SPOONACULAR_API_KEY:
        print("\n" + "="*70)
        print("ERROR: SPOONACULAR_API_KEY not found in .env file!")
        print("Please add your API key to the .env file")
        print("Get a free key at: https://spoonacular.com/food-api")
        print("="*70 + "\n")
        return False

    if SPOONACULAR_API_KEY == 'YOUR_NEW_API_KEY_HERE':
        print("\n" + "="*70)
        print("WARNING: Using placeholder API key!")
        print("Please replace with your actual Spoonacular API key in .env file")
        print("Get a free key at: https://spoonacular.com/food-api")
        print("The app will use fallback recipes until you add a valid key")
        print("="*70 + "\n")
        return False

    # Test the API key
    try:
        print("Testing Spoonacular API connection...")
        test_url = 'https://api.spoonacular.com/recipes/complexSearch'
        test_response = requests.get(
            test_url,
            params={'apiKey': SPOONACULAR_API_KEY, 'query': 'test', 'number': 1},
            timeout=5
        )

        if test_response.status_code == 200:
            quota_left = test_response.headers.get('X-Api-Quota-Left', 'unknown')
            print(f"✓ API Key Valid! Quota remaining: {quota_left}")
            return True
        elif test_response.status_code == 401:
            print("\n" + "="*70)
            print("ERROR: Invalid or expired Spoonacular API key!")
            print("Please check your API key in the .env file")
            print("Get a new free key at: https://spoonacular.com/food-api")
            print("The app will use fallback recipes until you add a valid key")
            print("="*70 + "\n")
            return False
        elif test_response.status_code == 402:
            print("\n" + "="*70)
            print("WARNING: API quota exceeded!")
            print("Your daily API limit has been reached")
            print("The app will use fallback recipes until quota resets")
            print("="*70 + "\n")
            return False
        else:
            print(f"WARNING: Unexpected API response: {test_response.status_code}")
            return False
    except Exception as e:
        print(f"WARNING: Could not validate API key: {str(e)}")
        return False

# Perform API validation on startup
print("\n" + "="*70)
print("AI CULINARY ASSISTANT - Starting Up")
print("="*70)
validate_api_key()
print("="*70 + "\n")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API connectivity"""
    health_status = {
        'status': 'healthy',
        'api_key_configured': bool(SPOONACULAR_API_KEY and SPOONACULAR_API_KEY != 'YOUR_NEW_API_KEY_HERE'),
        'spoonacular_api': 'unknown'
    }

    # Test Spoonacular API connection
    if SPOONACULAR_API_KEY and SPOONACULAR_API_KEY != 'YOUR_NEW_API_KEY_HERE':
        try:
            test_url = 'https://api.spoonacular.com/recipes/complexSearch'
            test_response = requests.get(
                test_url,
                params={'apiKey': SPOONACULAR_API_KEY, 'query': 'test', 'number': 1},
                timeout=5
            )
            if test_response.status_code == 200:
                health_status['spoonacular_api'] = 'connected'
                health_status['api_quota_left'] = test_response.headers.get('X-Api-Quota-Left', 'unknown')
            elif test_response.status_code == 401:
                health_status['spoonacular_api'] = 'invalid_key'
                health_status['status'] = 'degraded'
            elif test_response.status_code == 402:
                health_status['spoonacular_api'] = 'quota_exceeded'
                health_status['status'] = 'degraded'
            else:
                health_status['spoonacular_api'] = f'error_{test_response.status_code}'
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['spoonacular_api'] = f'connection_failed: {str(e)}'
            health_status['status'] = 'degraded'
    else:
        health_status['spoonacular_api'] = 'not_configured'
        health_status['status'] = 'degraded'

    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

@app.route('/api/identify', methods=['POST'])
def identify_food():
    if 'image' not in request.files and 'image' not in request.json:
        return jsonify({'error': 'No image provided'}), 400

    try:
        # Handle file upload or base64 image
        if 'image' in request.files:
            image_file = request.files['image']
            recognition_result = food_recognizer.recognize_food(image_file)
        else:
            # Handle base64 encoded image
            base64_image = request.json.get('image', '')
            recognition_result = food_recognizer.recognize_food(base64_image)

        if not recognition_result['success']:
            return jsonify({'error': recognition_result['error']}), 500

        food_name = recognition_result['food_name']

        # Check if OpenAI provided complete recipe (ingredients + instructions)
        if ('ingredients' in recognition_result and recognition_result['ingredients'] and
            'instructions' in recognition_result and recognition_result['instructions']):
            # Use complete recipe from OpenAI Vision
            print("Using complete recipe from OpenAI Vision")
            recipe_info = {
                "name": food_name,
                "ingredients": recognition_result['ingredients'],
                "instructions": recognition_result['instructions']
            }
            # Add additional info if available
            if 'prep_time' in recognition_result:
                recipe_info['prep_time'] = recognition_result['prep_time']
            if 'cook_time' in recognition_result:
                recipe_info['cook_time'] = recognition_result['cook_time']
            if 'cuisine' in recognition_result:
                recipe_info['cuisine'] = recognition_result['cuisine']
            if 'servings' in recognition_result:
                recipe_info['servings'] = recognition_result['servings']
            if 'difficulty' in recognition_result:
                recipe_info['difficulty'] = recognition_result['difficulty']
        elif 'ingredients' in recognition_result and recognition_result['ingredients']:
            # OpenAI provided ingredients but no instructions - fetch instructions
            print("Using ingredients from OpenAI Vision, fetching instructions")
            recipe_info = {
                "name": food_name,
                "ingredients": recognition_result['ingredients'],
                "instructions": []
            }
            # Get cooking instructions from recipe API
            full_recipe = get_recipe(food_name)
            if full_recipe and 'instructions' in full_recipe:
                recipe_info['instructions'] = full_recipe['instructions']
        else:
            # Get full recipe information from API or fallback
            recipe_info = get_recipe(food_name)

        return jsonify({
            'success': True,
            'food': food_name,
            'confidence': recognition_result['confidence'],
            'recipe': recipe_info,
            'source': 'OpenAI Vision' if 'ingredients' in recognition_result and recognition_result['ingredients'] else 'Spoonacular/Fallback'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return app.send_static_file(path)
    return app.send_static_file('index.html')

if __name__ == '__main__':
    # Using port 5001 instead of 5000 (port 5000 is often used by macOS AirPlay Receiver)
    app.run(debug=True, host='0.0.0.0', port=5001)