import os
import httpx
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_CLAIMS = os.getenv("AIRTABLE_TABLE_CLAIMS", "Claims")
AIRTABLE_TABLE_INTERACTIONS = os.getenv("AIRTABLE_TABLE_INTERACTIONS", "Interactions")

def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to digits only.
    Examples:
      "(555) 123-4567" -> "5551234567"
      "+1-555-123-4567" -> "15551234567"
    """
    return ''.join(filter(str.isdigit, phone))


class AirtableService:
    def __init__(self):
        if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
            raise ValueError("Airtable API Key and Base ID must be set in .env")
        
        self.base_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}"
        self.headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json"
        }
        # Persistent async client for connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=10.0
        )

    async def close(self):
        """Close the HTTP client. Call on app shutdown."""
        await self.client.aclose()

    async def find_customer_by_phone(self, phone_number: str):
        """
        Finds a customer by their phone number.
        Returns the first matching claim or None.
        
        NOTE: Current design assumes one claim per customer for demo simplicity.
        For production, this would return all claims or use a relational schema.
        """
        # Input validation
        if not phone_number or not isinstance(phone_number, str):
            return None
        
        # Normalize to digits only for consistent matching
        normalized_phone = normalize_phone_number(phone_number)
        
        if not normalized_phone:
            return None
        
        # Query Airtable with formula filter
        formula = f"{{Phone Number}} = '{normalized_phone}'"
        params = {"filterByFormula": formula}
        
        response = await self.client.get(f"/{AIRTABLE_TABLE_CLAIMS}", params=params)
        response.raise_for_status()
        
        data = response.json()
        records = data.get("records", [])
        
        if records:
            record = records[0]["fields"]  # Return first match only
            return {
                "firstName": record.get("First Name"),
                "lastName": record.get("Last Name"),
                "claimStatus": record.get("Claim Status")
            }
        
        return None

    async def log_interaction(self, caller_name: str, summary: str, sentiment: str):
        """
        Logs the interaction details to Airtable.
        """
        # Input validation
        if not caller_name or not summary or not sentiment:
            raise ValueError("caller_name, summary, and sentiment are required")
        
        # Validate sentiment value
        valid_sentiments = ["Positive", "Neutral", "Negative"]
        if sentiment not in valid_sentiments:
            raise ValueError(f"sentiment must be one of {valid_sentiments}")
        
        payload = {
            "records": [{
                "fields": {
                    "Caller Name": caller_name,
                    "Call Summary": summary,
                    "Sentiment": sentiment
                }
            }]
        }
        
        response = await self.client.post(f"/{AIRTABLE_TABLE_INTERACTIONS}", json=payload)
        response.raise_for_status()
        
        return response.json()
