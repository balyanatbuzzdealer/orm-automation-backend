from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
import scraper  # Import the updated scraper.py

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

    if "status" in results and results["status"] == "error":
        return results  # Return the error message if any

    # Properly handle the list of results
    return {
        "status": "success",
        "results": results.get("results", [])
    }
