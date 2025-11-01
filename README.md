# AI Culinary Assistant

An AI-powered culinary assistant that can identify food from images and provide detailed ingredients and cooking instructions.

## Features

- 📸 Upload food images for automatic identification
- 🥘 Get detailed ingredients list
- 👨‍🍳 Receive step-by-step cooking instructions
- 🎨 Simple and intuitive drag-and-drop interface
- ♻️ Graceful fallback with default recipes
- 🔍 API health monitoring
- 🔄 Automatic retry logic for API calls

## Quick Start

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Configure API Key (Optional but Recommended)

Get a FREE Spoonacular API key:
1. Visit: https://spoonacular.com/food-api
2. Sign up for free account (150 requests/day)
3. Copy your API key
4. Update `.env` file:
   ```
   SPOONACULAR_API_KEY=your_actual_api_key_here
   ```

**Note:** App works without API key using fallback recipes!

### 3. Run the Application

```bash
python3 app.py
```

### 4. Open in Browser

```
http://localhost:5001
```

**Note:** Using port **5001** instead of 5000 (port 5000 conflicts with macOS AirPlay Receiver)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/api/health` | GET | Check API status and connectivity |
| `/api/identify` | POST | Identify food from uploaded image |

## Usage

1. Open http://localhost:5001 in your browser
2. Drag & drop a food image or click to browse
3. Click "Upload Image"
4. View identified food, ingredients, and cooking instructions

## Technologies Used

- **Backend:** Flask (Python)
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Image Recognition:** Spoonacular Food API
- **Image Processing:** Pillow (PIL)
- **Styling:** Google Fonts (Poppins)

## Troubleshooting

### Port 5000 Already in Use
- App now uses port **5001** by default
- On macOS, port 5000 is often used by AirPlay Receiver
- To use a different port, edit `app.py` line 169

### API Key Issues
- Check `/api/health` endpoint for API status
- See `API_SETUP_GUIDE.md` for detailed setup instructions
- App works with fallback recipes if API key is not configured

### Server Not Starting
```bash
# Kill any existing Flask processes
pkill -f "python3 app.py"

# Restart the server
python3 app.py
```

## Project Structure

```
.
├── app.py                    # Flask application & routes
├── food_recognition.py       # Food recognition & recipe logic
├── requirements.txt          # Python dependencies
├── .env                     # API keys (not in git)
├── .gitignore               # Git ignore rules
├── API_SETUP_GUIDE.md       # Detailed API setup guide
├── README.md                # This file
└── frontend/
    ├── index.html           # Main HTML page
    ├── script.js            # Frontend JavaScript
    └── styles.css           # Styling
```

## Documentation

- **API Setup:** See `API_SETUP_GUIDE.md`
- **Health Check:** Visit http://localhost:5001/api/health

## License

This project is for educational purposes.