# TDS Virtual TA

A virtual Teaching Assistant for the Tools in Data Science course at IIT Madras.

## Features
- Scrapes Discourse forum data
- Provides AI-powered answers to student questions
- RESTful API interface
- Supports image attachments

## Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your OpenAI API key in `.env`
4. Run scraper: `python scraper.py`
5. Start API: `python app.py`

## API Usage
curl "https://your-app-url.com/api/"
-H "Content-Type: application/json"
-d "{"question": "Your question here"}"

## License
MIT License