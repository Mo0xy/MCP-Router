import asyncio
import logging
from colorama import Fore
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import SamplingMessage, TextContent
from dbAccess import get_candidate_skills_data, get_job_requirements
from core.openrouter import OpenRouterClient

# Configure logging for diagnostics
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
server = FastMCP("InterviewBot", log_level="INFO")

def safe_extract(result, key: str) -> str:
    """
    Safely extracts a string from a DB query result.
    Handles cases: None, int, string, list/tuple/dict.
    """
    if result is None:
        return "Data not available"
    if isinstance(result, int):
        return "Data not available"
    if isinstance(result, str):
        return result.strip()
    if isinstance(result, dict):
        return str(result.get(key, "Data not available")).strip()
    if isinstance(result, (list, tuple)) and len(result) > 0:
        first = result[0]
        if isinstance(first, dict):
            return str(first.get(key, "Data not available")).strip()
        if isinstance(first, (list, tuple)) and len(first) > 0:
            return str(first[0]).strip()
        if isinstance(first, str):
            return first.strip()
    return "Data not available"

@server.tool(
    name="generate_interview_questions",
    description="Generates personalized interview questions for a candidate and a job description",
)
async def generate_interview_questions(candidate_id: str, job_id: str, context: Context, num_questions: int = 5):
    """
    Generates personalized interview questions
    based on the candidate's skills and the job description.
    """
    try:
        candidate_data = get_candidate_skills_data(candidate_id)
        job_data = get_job_requirements(job_id)

        skills_text = safe_extract(candidate_data, "semantic_profile")
        job_description = safe_extract(job_data, "jobdescription")

        prompt = f"""
You are an expert recruiter. Generate {num_questions} personalized interview questions
for the following candidate:

📌 **Candidate's Skills:**
{skills_text}

📌 **Job Description:**
{job_description}

Each question must include a brief explanation of what it evaluates.
If user talks in Italian, reply in Italian, in numbered list format.
"""
        
        # THIS IS THE KEY POINT - you must use the sampling callback
        # The MCP server should have access to a way to do sampling
        # This depends on how you have configured the FastMCP server
        
        # Option 1: If you have access to sampling in the server
        # result = await server.request_sampling(prompt, max_tokens=2000)
        # return result
        
        # Option 2: Return the prompt to be processed by the client

        result = await context.session.create_message(
            messages=[
                SamplingMessage(
                    role="user", content=TextContent(type="text", text=prompt)
                )
            ],
            max_tokens=4000,
            system_prompt="You are a helpful research assistant.",
        )
        
        print(f"\n{Fore.RED}Sampling result:", result.content)
        
        if result.content.type == "text":
            return result.content.text
        else:
            raise ValueError("Sampling failed")

    except Exception as e:
        # logger.error(f"Error in generate_interview_questions: {e}")
        print(f"Error during question generation: {str(e)}")
        return f"Error during question generation: {str(e)}"

if __name__ == "__main__":
    asyncio.run(server.run())
