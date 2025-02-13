from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import scraper  # Import scraper.py

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["https://orm-automation-frontend.vercel.app", "http://localhost:3000/"],
    allow_origins=["*"],
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
    
    # Prepare response with file paths (can be changed to URLs if hosted)
    file_paths = results.get("results", {})
    
    # Send the file paths (for demonstration)
    return {"status": "success", "files": file_paths}
