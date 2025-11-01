from PIL import Image
import io
import base64
import random
import requests
import os
import time
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Get API keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SPOONACULAR_API_KEY = os.getenv('SPOONACULAR_API_KEY')

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY and OPENAI_API_KEY != 'your-openai-api-key-here' else None

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

class FoodRecognizer:
    def __init__(self):
        # Fallback food classes if API fails
        self.food_classes = [
            "pizza", "pasta carbonara", "sushi", "burger", "taco",
            "fried rice", "curry", "steak", "salad", "soup",
            "pancakes", "ice cream", "chocolate cake", "apple pie", "sandwich",
            "butter chicken"
        ]

    def recognize_with_openai(self, base64_image):
        """Use OpenAI GPT-4 Vision to recognize food from image"""
        try:
            if not openai_client:
                print("OpenAI client not initialized")
                return None

            print("Using OpenAI Vision API for food recognition...")

            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using the faster mini model
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this food image and provide a VERY DETAILED professional recipe. Return a JSON response with:

1. "food_name": the exact name of the food/dish
2. "confidence": confidence score between 0 and 1
3. "ingredients": array of ingredients with PRECISE quantities and specifications (e.g., "2 cups all-purpose flour, sifted", "500g boneless chicken breast, cut into 1-inch cubes", "1 tbsp extra virgin olive oil")
4. "instructions": array of EXTREMELY DETAILED step-by-step cooking instructions with specific temperatures, timings, and techniques. MINIMUM 8-10 comprehensive steps. Include:
   - Exact temperatures (e.g., "Preheat oven to 375°F/190°C")
   - Precise cooking times (e.g., "Cook for 8-10 minutes until golden brown")
   - Specific techniques (e.g., "Stir constantly using a wooden spoon")
   - Visual cues (e.g., "until mixture thickens and coats the back of a spoon")
   - Professional tips (e.g., "Let meat rest for 5 minutes before slicing")
5. "cuisine": type of cuisine (e.g., "Italian", "Indian", "Mexican")
6. "prep_time": estimated preparation time (e.g., "20 minutes")
7. "cook_time": estimated cooking time (e.g., "30 minutes")
8. "servings": number of servings (e.g., "4 servings")
9. "difficulty": difficulty level ("Easy", "Medium", "Hard")

IMPORTANT:
- Make instructions AS DETAILED AS POSSIBLE with specific measurements, times, and temperatures
- Each instruction should be complete and actionable
- Include chef's tips and important notes
- Provide enough detail so a beginner could successfully make this dish

Return ONLY valid JSON, nothing else."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2500
            )

            result_text = response.choices[0].message.content.strip()
            print(f"OpenAI Response: {result_text}")

            # Parse JSON response
            try:
                # Remove markdown code blocks if present
                if result_text.startswith("```"):
                    result_text = result_text.split("```")[1]
                    if result_text.startswith("json"):
                        result_text = result_text[4:]
                    result_text = result_text.strip()

                result_json = json.loads(result_text)

                return {
                    "success": True,
                    "food_name": result_json.get("food_name", "unknown food"),
                    "confidence": float(result_json.get("confidence", 0.85)),
                    "ingredients": result_json.get("ingredients", []),
                    "instructions": result_json.get("instructions", []),
                    "cuisine": result_json.get("cuisine", ""),
                    "prep_time": result_json.get("prep_time", ""),
                    "cook_time": result_json.get("cook_time", ""),
                    "servings": result_json.get("servings", ""),
                    "difficulty": result_json.get("difficulty", "")
                }
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                # Fallback: extract food name from text response
                food_name = result_text.split('\n')[0] if result_text else "unknown food"
                return {
                    "success": True,
                    "food_name": food_name,
                    "confidence": 0.75,
                    "ingredients": [],
                    "cuisine": ""
                }

        except Exception as e:
            print(f"OpenAI Vision error: {str(e)}")
            return None

    def recognize_food(self, image_data):
        """
        Recognize food from image data using OpenAI Vision (preferred) or Spoonacular API (fallback)
        """
        try:
            # Handle different image input formats and convert to base64
            if isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))
                img_bytes = io.BytesIO()
                image.save(img_bytes, format='JPEG')
                img_bytes = img_bytes.getvalue()
                base64_image = base64.b64encode(img_bytes).decode('utf-8')
            elif isinstance(image_data, str) and image_data.startswith('data:image'):
                # Handle base64 encoded image
                base64_image = image_data.split(',')[1]
                img_bytes = base64.b64decode(base64_image)
                image = Image.open(io.BytesIO(img_bytes))
            else:
                # Assume it's a file-like object
                image = Image.open(image_data)
                img_bytes = io.BytesIO()
                image.save(img_bytes, format='JPEG')
                img_bytes = img_bytes.getvalue()
                base64_image = base64.b64encode(img_bytes).decode('utf-8')

            # Try OpenAI Vision API first (more accurate)
            if openai_client:
                print("Trying OpenAI Vision API...")
                openai_result = self.recognize_with_openai(base64_image)
                if openai_result and openai_result.get('success'):
                    print(f"✓ OpenAI recognized: {openai_result['food_name']}")
                    return openai_result
            
            # Use Spoonacular API for food recognition
            try:
                # Check if API key is configured
                if not SPOONACULAR_API_KEY or SPOONACULAR_API_KEY == 'YOUR_NEW_API_KEY_HERE':
                    print("API key not configured - using fallback")
                    random_food = random.choice(self.food_classes)
                    return {
                        "success": True,
                        "food_name": random_food,
                        "confidence": 0.7,
                        "note": "API key not configured - using fallback"
                    }

                # Prepare the image file for the API request
                files = {'file': ('image.jpg', img_bytes, 'image/jpeg')}

                print(f"Making API request to Spoonacular with API key: {SPOONACULAR_API_KEY[:5]}...")

                # Make the API request with retry logic
                api_key = SPOONACULAR_API_KEY.strip()
                url = f'https://api.spoonacular.com/food/images/classify?apiKey={api_key}'

                for attempt in range(MAX_RETRIES):
                    try:
                        response = requests.post(
                            url,
                            files=files,
                            timeout=10
                        )

                        print(f"API Response Status: {response.status_code} (attempt {attempt + 1}/{MAX_RETRIES})")

                        # Check if the request was successful
                        if response.status_code == 200:
                            result = response.json()
                            print(f"API Result: {result}")

                            # Spoonacular API returns different format than expected
                            # Check for the correct fields based on API documentation
                            if 'category' in result:
                                food_name = result['category']
                                confidence = result.get('probability', 0.8)
                            elif 'classification' in result:
                                food_name = result['classification']['name']
                                confidence = result['classification'].get('confidence', 0.8)
                            else:
                                # Try to extract any food name from the response
                                food_name = next((key for key in result.keys() if key not in ['status', 'code', 'message']), 'unknown food')
                                confidence = 0.7

                            print(f"Identified food: {food_name} with confidence {confidence}")
                            return {
                                "success": True,
                                "food_name": food_name,
                                "confidence": confidence
                            }
                        elif response.status_code == 401:
                            print(f"API Error 401: Invalid API key")
                            print(f"Response: {response.text}")
                            break  # Don't retry on auth errors
                        elif response.status_code == 402:
                            print(f"API Error 402: Quota exceeded")
                            print(f"Response: {response.text}")
                            break  # Don't retry on quota errors
                        elif response.status_code >= 500 and attempt < MAX_RETRIES - 1:
                            # Server error - retry
                            print(f"Server error, retrying in {RETRY_DELAY}s...")
                            time.sleep(RETRY_DELAY)
                            continue
                        else:
                            print(f"API Error: {response.status_code}, {response.text}")
                            break

                    except requests.exceptions.Timeout:
                        if attempt < MAX_RETRIES - 1:
                            print(f"Request timeout, retrying in {RETRY_DELAY}s...")
                            time.sleep(RETRY_DELAY)
                            continue
                        else:
                            print(f"Request timeout after {MAX_RETRIES} attempts")
                            break
                    except requests.exceptions.ConnectionError:
                        if attempt < MAX_RETRIES - 1:
                            print(f"Connection error, retrying in {RETRY_DELAY}s...")
                            time.sleep(RETRY_DELAY)
                            continue
                        else:
                            print(f"Connection error after {MAX_RETRIES} attempts")
                            break

                # If we get here, API call failed - fall back to random food selection
                print(f"Falling back to random food selection")
                random_food = random.choice(self.food_classes)
                return {
                    "success": True,
                    "food_name": random_food,
                    "confidence": 0.7,
                    "note": "Using fallback due to API error"
                }

            except Exception as api_error:
                # If there's an error with the API call, fall back to random food selection
                print(f"API Exception: {str(api_error)}")
                random_food = random.choice(self.food_classes)
                return {
                    "success": True,
                    "food_name": random_food,
                    "confidence": 0.7,
                    "note": "Using fallback due to API error"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Function to get recipe information based on food name
def get_recipe(food_name):
    """
    Get recipe information for a given food name using Spoonacular API
    """
    try:
        # Check if API key is configured
        if not SPOONACULAR_API_KEY or SPOONACULAR_API_KEY == 'YOUR_NEW_API_KEY_HERE':
            print(f"API key not configured - using default recipe for {food_name}")
            return get_default_recipe(food_name)

        # Search for recipes using Spoonacular API with retry logic
        search_url = 'https://api.spoonacular.com/recipes/complexSearch'
        search_params = {
            'apiKey': SPOONACULAR_API_KEY,
            'query': food_name,
            'number': 1,  # Get just one recipe
            'instructionsRequired': True,
            'fillIngredients': True,
            'addRecipeInformation': True
        }

        for attempt in range(MAX_RETRIES):
            try:
                search_response = requests.get(search_url, params=search_params, timeout=10)

                if search_response.status_code == 200:
                    break  # Success, exit retry loop
                elif search_response.status_code == 401:
                    print(f"Invalid API key for recipe search")
                    return get_default_recipe(food_name)
                elif search_response.status_code == 402:
                    print(f"API quota exceeded for recipe search")
                    return get_default_recipe(food_name)
                elif search_response.status_code >= 500 and attempt < MAX_RETRIES - 1:
                    print(f"Server error in recipe search, retrying in {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    print(f"Recipe search API error: {search_response.status_code}")
                    return get_default_recipe(food_name)

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"Connection error in recipe search, retrying in {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    print(f"Connection error after {MAX_RETRIES} attempts")
                    return get_default_recipe(food_name)

        if search_response.status_code == 200:
            search_data = search_response.json()
            
            if search_data['results'] and len(search_data['results']) > 0:
                recipe_id = search_data['results'][0]['id']
                
                # Get detailed recipe information
                recipe_url = f'https://api.spoonacular.com/recipes/{recipe_id}/information'
                recipe_params = {
                    'apiKey': SPOONACULAR_API_KEY,
                    'includeNutrition': False
                }
                
                recipe_response = requests.get(recipe_url, params=recipe_params)
                
                if recipe_response.status_code == 200:
                    recipe_data = recipe_response.json()
                    
                    # Extract ingredients
                    ingredients = []
                    for ingredient in recipe_data.get('extendedIngredients', []):
                        ingredients.append(ingredient.get('original', ''))
                    
                    # Extract instructions
                    instructions = []
                    if 'analyzedInstructions' in recipe_data and recipe_data['analyzedInstructions']:
                        for step in recipe_data['analyzedInstructions'][0].get('steps', []):
                            instructions.append(step.get('step', ''))
                    else:
                        # Fallback to summary if no instructions available
                        instructions = [recipe_data.get('summary', 'No instructions available')]
                    
                    return {
                        "name": recipe_data.get('title', food_name.title()),
                        "ingredients": ingredients,
                        "instructions": instructions
                    }
        
        # If API call fails or no results, fall back to default recipes
        print(f"Falling back to default recipe for {food_name}")
        return get_default_recipe(food_name)
        
    except Exception as e:
        print(f"Error getting recipe: {str(e)}")
        return get_default_recipe(food_name)

# Function to get default recipe if API fails
def get_default_recipe(food_name):
    """
    Get a default recipe if the API call fails
    """
    # Sample recipes for demo purposes
    recipes = {
        "butter chicken": {
            "name": "Butter Chicken (Murgh Makhani)",
            "ingredients": [
                "800g boneless chicken thighs, cut into bite-sized pieces",
                "2 tbsp lemon juice",
                "3 cloves garlic, minced",
                "1 tbsp ginger, grated",
                "2 tsp garam masala",
                "1 tsp ground cumin",
                "1 tsp ground turmeric",
                "1 tsp ground coriander",
                "1 cup plain yogurt",
                "2 tbsp vegetable oil",
                "2 tbsp butter",
                "1 large onion, finely chopped",
                "2 tbsp tomato paste",
                "1 can (400g) tomato sauce",
                "1 cup heavy cream",
                "Fresh cilantro for garnish",
                "Basmati rice for serving"
            ],
            "instructions": [
                "In a large bowl, combine chicken with lemon juice, garlic, ginger, garam masala, cumin, turmeric, coriander, and yogurt. Marinate for at least 1 hour, preferably overnight.",
                "Heat oil in a large skillet over medium-high heat. Add marinated chicken and cook until browned, about 5-7 minutes.",
                "Remove chicken and set aside. In the same pan, add butter and onions. Cook until onions are soft and translucent, about 3-4 minutes.",
                "Add tomato paste and cook for 2 minutes. Add tomato sauce and bring to a simmer.",
                "Return chicken to the pan and simmer for 15 minutes on low heat.",
                "Stir in heavy cream and simmer for another 5 minutes until the sauce thickens.",
                "Garnish with fresh cilantro and serve hot with basmati rice."
            ]
        },
        "pizza": {
            "name": "Homemade Pizza",
            "ingredients": [
                "500g pizza dough", 
                "200g tomato sauce", 
                "250g mozzarella cheese", 
                "2 tbsp olive oil",
                "1 tsp dried oregano",
                "Toppings of your choice (pepperoni, vegetables, etc.)"
            ],
            "instructions": [
                "Preheat your oven to 475°F (245°C).",
                "Roll out the pizza dough on a floured surface.",
                "Transfer the dough to a pizza stone or baking sheet.",
                "Spread tomato sauce evenly over the dough, leaving a small border.",
                "Sprinkle mozzarella cheese over the sauce.",
                "Add your desired toppings.",
                "Drizzle with olive oil and sprinkle with oregano.",
                "Bake for 10-12 minutes until the crust is golden and cheese is bubbly.",
                "Let cool for a few minutes before slicing and serving."
            ]
        }
    }
    
    # Default recipe for foods not in our database
    default_recipe = {
        "name": food_name.title(),
        "ingredients": [
            "Ingredient 1",
            "Ingredient 2",
            "Ingredient 3",
            "Ingredient 4",
            "Ingredient 5"
        ],
        "instructions": [
            "Step 1: Prepare the ingredients",
            "Step 2: Cook according to your preferred method",
            "Step 3: Combine all ingredients",
            "Step 4: Serve and enjoy"
        ]
    }
    
    return recipes.get(food_name.lower(), default_recipe)