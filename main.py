from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
import scraper  # Import scraper.py

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://orm-automation-frontend.vercel.app"],  # Replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

@app.post("/")
async def scrape(
    country: str = Form(...),
    search_terms: str = Form(...),
    num_results: int = Form(...)
):
    """Calls scraper only once, keeping a single browser session open."""
    results = scraper.scrape_google_search(search_terms, country, num_results)
    return {"results": results}
