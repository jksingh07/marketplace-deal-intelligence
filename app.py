import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import uvicorn
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field

# Add src to path so we can import modules
sys.path.append(str(Path(__file__).parent / "src"))

from stage4.runner import run_stage4
from common.scoring.flipability import calculate_flipability
from stage7.llm_pricer import estimate_price_with_llm

# Initialize FastAPI app
app = FastAPI(
    title="Marketplace Deal Intelligence API",
    description="API for extracting intelligence from car listings and calculating flipability scores.",
    version="1.0.0"
)

# --- Pydantic Models ---

class ListingInput(BaseModel):
    listing_id: str = Field(..., description="Unique identifier for the listing")
    title: str = Field(..., description="Title of the listing")
    description: str = Field(..., description="Full description text of the listing")
    price: Optional[float] = Field(None, description="Asking price")
    mileage: Optional[float] = Field(None, description="Vehicle mileage")
    vehicle_type: Optional[str] = Field("car", description="Type of vehicle (car, bike, etc.)")
    
    class Config:
        extra = "allow"  # Allow other fields to be passed through

class MarketDataInput(BaseModel):
    asking_price: Optional[float] = Field(None, description="Asking price of the vehicle")
    estimated_market_price_p50: float = Field(..., description="Estimated market price (P50)")
    comps_used_count: int = Field(..., description="Number of comparable listings found")
    confidence: Optional[float] = Field(None, description="Confidence score of the market data")

class EvaluateRequest(BaseModel):
    listing: ListingInput
    market_data: Optional[MarketDataInput] = Field(None, description="Market data for flipability scoring. If not provided, LLM will estimate market price.")
    skip_llm: bool = Field(False, description="If True, skips LLM extraction and runs only guardrails (faster, cheaper)")

# --- Endpoints ---

@app.get("/")
def health_check():
    return {"status": "online", "service": "Marketplace Deal Intelligence API"}

@app.post("/analyze", summary="Run Stage 4 Analysis (Description Intelligence)")
def analyze_listing_endpoint(
    listing: ListingInput, 
    skip_llm: bool = False
):
    """
    Analyzes a listing description to extract risks, modifications, and other intelligence.
    """
    try:
        # Convert Pydantic model to dict
        listing_dict = listing.model_dump()
        
        # Run Stage 4 pipeline
        result = run_stage4(
            listing=listing_dict,
            skip_llm=skip_llm,
            validate=True
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/score", summary="Calculate Flipability Score")
def calculate_score_endpoint(
    stage4_payload: Dict[str, Any] = Body(..., description="Payload from Stage 4 analysis"),
    market_data: MarketDataInput = Body(..., description="Market data inputs")
):
    """
    Calculates the Flipability Score based on Stage 4 analysis and Market Data.
    """
    try:
        # Prepare payloads
        s7_payload = market_data.model_dump()
        
        # Ensure asking_price is available (it might be in market_data or stage4_payload inputs)
        # But here we rely on market_data having it or the caller ensuring it.
        # If asking_price is None in s7_payload, we might fail or get a partial score.
        
        result = calculate_flipability(s7_payload, stage4_payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate", summary="Full Evaluation (Analysis + Score)")
def evaluate_deal_endpoint(request: EvaluateRequest):
    """
    Runs both Stage 4 Analysis and Flipability Scoring in one go.
    
    If `market_data` is NOT provided, it will use an LLM to estimate the market price 
    and then calculate the score.
    """
    try:
        # 1. Run Analysis
        listing_dict = request.listing.model_dump()
        stage4_result = run_stage4(
            listing=listing_dict,
            skip_llm=request.skip_llm,
            validate=True
        )
        
        response = {
            "analysis": stage4_result,
            "flipability": None,
            "market_data_source": "provided" if request.market_data else "llm_estimation"
        }
        
        # 2. Determine Market Data
        s7_payload = None
        
        if request.market_data:
            # Use provided market data
            s7_payload = request.market_data.model_dump()
        elif not request.skip_llm:
            # Estimate using LLM
            # We need the listing dict which has price, mileage, title, etc.
            llm_estimate = estimate_price_with_llm(listing_dict)
            
            # Map LLM result to s7_payload format
            s7_payload = {
                "estimated_market_price_p50": llm_estimate.get("estimated_market_price_p50", 0),
                "comps_used_count": llm_estimate.get("comps_used_count", 0),
                "confidence": llm_estimate.get("confidence", 0.5),
                "asking_price": listing_dict.get("price"),
                "estimation_details": llm_estimate # Include extra details for debugging
            }
            response["market_data_estimation"] = llm_estimate
        
        # 3. Calculate Score (if we have market data)
        if s7_payload:
            # Ensure asking_price is available
            if "asking_price" not in s7_payload or s7_payload["asking_price"] is None:
                s7_payload["asking_price"] = listing_dict.get("price")
            
            if s7_payload["asking_price"] is not None and s7_payload["estimated_market_price_p50"] > 0:
                flip_result = calculate_flipability(s7_payload, stage4_result["payload"])
                response["flipability"] = flip_result
            else:
                response["flipability_error"] = "Asking price or valid market price required for flipability score"
        else:
             response["flipability_error"] = "No market data provided and LLM estimation skipped/failed"
                
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting Marketplace Deal Intelligence API...")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
