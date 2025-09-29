import time
import logging
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# Configura logging per diagnostica
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("DocumentMCP", log_level="INFO")  # Cambiato da ERROR a INFO per più diagnostica

docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

@mcp.tool(
    name="read_doc",
    description="Read a document by its ID",
)
def read_doc(doc_id: str = Field(description="The ID of the document to read")) -> str:
    start_time = time.time()
    logger.info(f"Starting read_doc for doc_id: {doc_id}")
    
    try:
        result = docs.get(doc_id, "")
        execution_time = time.time() - start_time
        logger.info(f"read_doc completed in {execution_time:.2f}s for doc_id: {doc_id}")
        return result
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"read_doc failed after {execution_time:.2f}s for doc_id: {doc_id}, error: {e}")
        raise

@mcp.tool(
    name="edit_doc",
    description="Edit a document by its ID and content"
)
def edit_doc(doc_id: str = Field(description="The ID of the document to edit"), 
             content: str = Field(description="The new content of the document")) -> str:
    start_time = time.time()
    logger.info(f"Starting edit_doc for doc_id: {doc_id}, content_length: {len(content)}")
    
    try:
        if doc_id in docs:
            docs[doc_id] = content
            execution_time = time.time() - start_time
            logger.info(f"edit_doc completed in {execution_time:.2f}s for doc_id: {doc_id}")
            return f"Document {doc_id} successfully updated with new content"
        else:
            execution_time = time.time() - start_time
            logger.warning(f"edit_doc failed in {execution_time:.2f}s - doc_id not found: {doc_id}")
            return f"Document {doc_id} not found"
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"edit_doc failed after {execution_time:.2f}s for doc_id: {doc_id}, error: {e}")
        raise

@mcp.tool(
    name="duplicate_doc",
    description="Duplicate a document by its ID and return the duplicated content",
)
def duplicate_doc(doc_id: str = Field(description="The ID of the document to duplicate")) -> str:
    start_time = time.time()
    logger.info(f"Starting duplicate_doc for doc_id: {doc_id}")
    
    try:
        if doc_id not in docs:
            execution_time = time.time() - start_time
            logger.warning(f"duplicate_doc failed in {execution_time:.2f}s - doc_id not found: {doc_id}")
            return f"Document {doc_id} not found"
        
        original_content = docs[doc_id]
        
        # Crea un nuovo ID per il documento duplicato
        duplicate_id = f"{doc_id}_copy"
        counter = 1
        while duplicate_id in docs:
            duplicate_id = f"{doc_id}_copy_{counter}"
            counter += 1
        
        # Duplica il contenuto
        docs[duplicate_id] = original_content
        
        execution_time = time.time() - start_time
        logger.info(f"duplicate_doc completed in {execution_time:.2f}s for doc_id: {doc_id}, created: {duplicate_id}")
        
        return f"Document duplicated successfully. Original: {doc_id}, Duplicate: {duplicate_id}. Content: {original_content}"
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"duplicate_doc failed after {execution_time:.2f}s for doc_id: {doc_id}, error: {e}")
        raise

@mcp.tool(
    name="list_docs",
    description="List all available document IDs"
)
def list_docs() -> str:
    start_time = time.time()
    logger.info("Starting list_docs")
    
    try:
        doc_list = list(docs.keys())
        execution_time = time.time() - start_time
        logger.info(f"list_docs completed in {execution_time:.2f}s, found {len(doc_list)} documents")
        return f"Available documents: {', '.join(doc_list)}"
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"list_docs failed after {execution_time:.2f}s, error: {e}")
        raise

@mcp.resource(
    uri="docs://documents",
    name="get_all_doc_ids",
    description="Get all document IDs"
)
def get_all_doc_ids() -> list[str]:
    start_time = time.time()
    logger.info("Starting get_all_doc_ids resource")
    
    try:
        doc_list = list(docs.keys())
        execution_time = time.time() - start_time
        logger.info(f"get_all_doc_ids resource completed in {execution_time:.2f}s, returning {len(doc_list)} documents")
        return doc_list
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"get_all_doc_ids resource failed after {execution_time:.2f}s, error: {e}")
        raise

@mcp.resource(
    uri="docs://documents/{doc_id}",
    name="get_doc_content",
    description="Get the contents of a document by its ID"
)
def get_doc_content(doc_id: str) -> str:
    start_time = time.time()
    logger.info(f"Starting get_doc_content resource for doc_id: {doc_id}")
    
    try:
        content = docs.get(doc_id, "")
        execution_time = time.time() - start_time
        logger.info(f"get_doc_content resource completed in {execution_time:.2f}s for doc_id: {doc_id}")
        return content
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"get_doc_content resource failed after {execution_time:.2f}s for doc_id: {doc_id}, error: {e}")
        raise

@mcp.prompt()
def rewrite_doc_in_markdown(doc_id: str) -> str:
    """Rewrite a document in markdown format"""
    start_time = time.time()
    logger.info(f"Starting rewrite_doc_in_markdown prompt for doc_id: {doc_id}")
    
    try:
        content = docs.get(doc_id, "")
        if not content:
            logger.warning(f"Document {doc_id} not found for markdown rewrite")
            return f"Document {doc_id} not found"
        
        markdown_content = f"# {doc_id}\n\n{content}"
        execution_time = time.time() - start_time
        logger.info(f"rewrite_doc_in_markdown prompt completed in {execution_time:.2f}s for doc_id: {doc_id}")
        return markdown_content
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"rewrite_doc_in_markdown prompt failed after {execution_time:.2f}s for doc_id: {doc_id}, error: {e}")
        raise

@mcp.prompt()
def summarize_doc(doc_id: str) -> str:
    """Summarize a document"""
    start_time = time.time()
    logger.info(f"Starting summarize_doc prompt for doc_id: {doc_id}")
    
    try:
        content = docs.get(doc_id, "")
        if not content:
            logger.warning(f"Document {doc_id} not found for summarization")
            return f"Document {doc_id} not found"
        
        # Simple summary by taking the first 100 characters
        summary = content[:100] + ("..." if len(content) > 100 else "")
        execution_time = time.time() - start_time
        logger.info(f"summarize_doc prompt completed in {execution_time:.2f}s for doc_id: {doc_id}")
        return f"Summary of {doc_id}: {summary}"
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"summarize_doc prompt failed after {execution_time:.2f}s for doc_id: {doc_id}, error: {e}")
        raise

# Funzione di diagnostica per verificare lo stato del server
@mcp.tool(
    name="server_status",
    description="Get server status and document statistics"
)
def server_status() -> str:
    """Restituisce lo stato del server e statistiche sui documenti"""
    start_time = time.time()
    logger.info("Starting server_status check")
    
    try:
        status = {
            "server": "healthy",
            "total_documents": len(docs),
            "document_list": list(docs.keys()),
            "timestamp": time.time(),
            "uptime_check": "OK"
        }
        
        execution_time = time.time() - start_time
        logger.info(f"server_status completed in {execution_time:.2f}s")
        
        return f"Server Status: {status}"
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"server_status failed after {execution_time:.2f}s, error: {e}")
        raise


if __name__ == "__main__":
    logger.info("Starting DocumentMCP server...")
    logger.info(f"Available documents: {list(docs.keys())}")
    mcp.run(transport="stdio")