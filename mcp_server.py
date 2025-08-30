# If 'mcp' is a local module, adjust the import path accordingly, for example:
# from server.fastmcp import FastMCP
# Or, if 'fastmcp.py' is in the same directory:
# from fastmcp import FastMCP

# If 'mcp' is an external package, install it:
# pip install mcp

# Example fallback if 'fastmcp.py' is in the same folder:
# from mcp_server import FastMCP
from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("DocumentMCP", log_level="ERROR")


docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

# TODO: Write a tool to read a doc
@mcp.tool(
    name="read_doc",
    description="Read a document by its ID",
    # mimeType="application/json"
)
def read_doc(doc_id: str = Field(description="The ID of the document to read")) -> str:
    return docs.get(doc_id, "")

# TODO: Write a tool to edit a doc
@mcp.tool(
    name="edit_doc",
    description="Edit a document by its ID and content"
)
def edit_doc(doc_id: str = Field(description="The ID of the document to edit"), content: str = Field(description="The new content of the document")) -> bool:
    if doc_id in docs:
        docs[doc_id] = content
        return True
    return False


""""""

# TODO: Write a resource to return all doc id's
@mcp.resource(
    uri="docs://documents",
    name= "get_all_doc_ids",
    description="Get all document IDs"
)
def get_all_doc_ids() -> list[str]:
    return list(docs.keys())

# TODO: Write a resource to return the contents of a particular doc
@mcp.resource(
    uri="docs://documents/{doc_id}",
    name= "get_doc_content",
    description="Get the contents of a document by its ID"
)
def get_doc_content(doc_id: str) -> str:
    return docs.get(doc_id, "")

# TODO: Write a prompt to rewrite a doc in markdown format
@mcp.prompt()
def rewrite_doc_in_markdown(doc_id: str) -> str:
    content = docs.get(doc_id, "")
    return f"# {doc_id}\n\n{content}"

# TODO: Write a prompt to summarize a doc
@mcp.prompt()
def summarize_doc(doc_id: str) -> str:
    content = docs.get(doc_id, "")
    # Simple summary by taking the first 100 characters
    return content[:100] + "..."


if __name__ == "__main__":
    mcp.run(transport="stdio")
