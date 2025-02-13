from fastapi import FastAPI, Form
import scraper  # Import scraper.py

app = FastAPI()

@app.post("/scrape")
async def scrape(
    country: str = Form(...),
    search_terms: str = Form(...),
    num_results: int = Form(...)
):
    """Calls scraper only once, keeping a single browser session open."""
    results = scraper.scrape_google_search(search_terms, country, num_results)
    return {"results": results}
