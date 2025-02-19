from fastapi import FastAPI, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import scraper  # Import scraper.py
from supabase import Client, create_client


url: str = "https://zqjmxfuneoaaqppnjzfd.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpxam14ZnVuZW9hYXFwcG5qemZkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk5NTcxMTcsImV4cCI6MjA1NTUzMzExN30.PFNYW-pwvMYB0JsR7h-HyV06Acadm1lSKvL7PMIuHLg"
supabase: Client = create_client(url, key)

# Initialize FastAPI app
app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})

        return {"login": "true"}
    except:
        return {"login": "false"}