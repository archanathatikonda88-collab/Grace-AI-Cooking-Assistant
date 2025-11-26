# Grace - AI Cooking Assistant Chatbot

## Overview

Grace helps you find recipes based on ingredients you have at home. Tell Grace what ingredients you have and your cooking skill level, and it will suggest recipes with photos and step-by-step instructions.

**Live Demo:** [https://grace-chatbot-234631291379.us-central1.run.app](https://grace-chatbot-234631291379.us-central1.run.app)

## Technologies Used

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python Flask
- **AI:** OpenAI GPT-4
- **Images:** Pexels API
- **Hosting:** Google Cloud Run

## How to Run the Project

1. Install Python 3.8+
2. Clone the project and navigate to folder
3. Install packages: `pip install -r requirements.txt`
4. Get free API keys from OpenAI and Pexels
5. Create `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_key_here
   PEXELS_API_KEY=your_key_here
   ```
6. Run: `python app.py`
7. Open browser: `http://localhost:5000`

## Example Input/Output

**Input:** 
- Ingredients: "chicken, rice"
- Difficulty: "Easy"

**Output:**
- Simple Chicken Rice Bowl (20 minutes)
- Easy Chicken Fried Rice (15 minutes)
- Each recipe includes photo and cooking instructions

---

*Built by [Your Name] - AI-powered cooking assistant*