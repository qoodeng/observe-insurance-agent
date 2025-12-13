from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from app.services.airtable_service import AirtableService
import json

app = FastAPI()

# Enable CORS for VAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Airtable Service
try:
    airtable_service = AirtableService()
except ValueError as e:
    print(f"Warning: Airtable service not initialized. {e}")
    airtable_service = None


@app.on_event("shutdown")
async def shutdown_event():
    """Close async HTTP client on shutdown."""
    if airtable_service:
        await airtable_service.close()


# --- Helper Functions ---

def parse_request_body(body: dict, *field_names: str) -> tuple[dict, str | None]:
    """
    Parse request body handling both VAPI format and direct JSON.
    Returns (args_dict, tool_call_id) where tool_call_id is None for direct requests.
    """
    # Handle VAPI format (nested in message.toolCalls)
    if "message" in body and body["message"].get("type") == "tool-calls":
        tool_call = body["message"]["toolCalls"][0]
        args_str = tool_call["function"]["arguments"]
        args = json.loads(args_str) if isinstance(args_str, str) else args_str
        return args, tool_call["id"]
    
    # Direct JSON format
    return body, None


def format_response(result: dict, tool_call_id: str | None) -> dict:
    """Format response for either VAPI or direct request."""
    if tool_call_id:
        return {"results": [{"toolCallId": tool_call_id, "result": json.dumps(result)}]}
    return result


# --- Endpoints ---

@app.get("/")
async def root():
    return {"status": "Observe Insurance Agent API is running"}


@app.post("/lookup-caller-data")
async def lookup_caller_data(request: Request):
    """Look up a caller's claim status by phone number."""
    if not airtable_service:
        raise HTTPException(status_code=503, detail="Airtable service unavailable")
    
    body = await request.json()
    args, tool_call_id = parse_request_body(body)
    phone_number = args.get("phone_number", "")
    
    # Validate
    if not phone_number:
        return format_response({"success": False, "error": "No phone number provided."}, tool_call_id)
    
    # Lookup
    customer = await airtable_service.find_customer_by_phone(phone_number)
    
    if customer:
        result = {"success": True, **customer}
    else:
        result = {"success": False, "error": "Record not found."}
    
    return format_response(result, tool_call_id)


@app.post("/log-call-summary")
async def log_call_summary(request: Request):
    """Log the call summary and sentiment at the end of the call."""
    if not airtable_service:
        raise HTTPException(status_code=503, detail="Airtable service unavailable")
    
    body = await request.json()
    args, tool_call_id = parse_request_body(body)
    
    try:
        await airtable_service.log_interaction(
            args.get("caller_name", ""),
            args.get("summary", ""),
            args.get("sentiment", "")
        )
        result = {"success": True}
    except Exception as e:
        print(f"Error logging interaction: {e}")
        result = {"success": False, "error": str(e)}
    
    return format_response(result, tool_call_id)
