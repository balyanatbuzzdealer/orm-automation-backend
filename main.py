from fastapi import FastAPI, Form
import os
from fastapi.middleware.cors import CORSMiddleware
import scraper  # Import scraper.py
import firebase_admin
from firebase_admin import credentials, firestore, storage

# Initialize Firebase Admin SDK
cred = credentials.Certificate(os.environ.get("FIRESTORE"))
firebase_admin.initialize_app(cred, {
    'storageBucket': 'orm-automation-app.appspot.com'  # Replace with your Firebase Storage bucket
})

# Initialize Firestore (if needed)
db = firestore.client()

# Initialize FastAPI app
app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with specific domains for security
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

@app.post("/scrape")
async def scrape(
    country: str = Form(...),
    search_terms: str = Form(...),
    num_results: int = Form(...)
):
    """Calls scraper only once, keeping a single browser session open."""
    print("You have called the scraper")
    results = scraper.scrape_google_search(search_terms, country, num_results)
    
    return {"status": "success", "files": results.get("results", {})}

