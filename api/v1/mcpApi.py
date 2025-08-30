from fastapi import FastAPI, Query, HTTPException
from api.v1.mcp_run import run_mcp, run_mcp_with_thread_safe
from fastapi.responses import RedirectResponse
import logging
import traceback

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP API", version="1.0.0")

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.post("/chat")
def generate_text(prompt: str = Query(..., description="Prompt text")):
    """
    Chat endpoint that uses the thread-safe version of MCP.
    """
    try:
        logger.info(f"Received prompt: {prompt[:100]}...")
        
        # Use the thread-safe version
        response = run_mcp(prompt)  # This now uses run_mcp_in_new_thread internally
        
        logger.info(f"Response generated successfully")
        return {"response": response}
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        logger.error(traceback.format_exc())
        
        # Return an HTTP error instead of crashing the API
        raise HTTPException(
            status_code=500, 
            detail=f"Error during processing: {str(e)}"
        )

@app.post("/chat_alternative")
def generate_text_alt(prompt: str = Query(..., description="Prompt text")):
    """
    Alternative endpoint that uses a different thread-safe strategy.
    """
    try:
        logger.info(f"Received prompt (alt): {prompt[:100]}...")
        
        # Use the alternative version
        response = run_mcp_with_thread_safe(prompt)
        
        logger.info(f"Alternative response generated successfully")
        return {"response": response}
        
    except Exception as e:
        logger.error(f"Error in alternative chat endpoint: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error during alternative processing: {str(e)}"
        )

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running"}