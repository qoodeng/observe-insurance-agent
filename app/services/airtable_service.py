import os
from pyairtable import Api
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
        self.api = Api(AIRTABLE_API_KEY)
        self.claims_table = self.api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_CLAIMS)
        self.interactions_table = self.api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_INTERACTIONS)

    def find_customer_by_phone(self, phone_number: str):
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
        
        # Note: Your Airtable should store phone numbers in normalized format (digits only)
        formula = f"{{Phone Number}} = '{normalized_phone}'"
        matches = self.claims_table.all(formula=formula)
        
        if matches:
            record = matches[0]["fields"]  # Return first match only
            return {
                "firstName": record.get("First Name"),
                "lastName": record.get("Last Name"),
                "claimStatus": record.get("Claim Status")
            }
            
            # TODO: For production with multiple claims per customer, return:
            # return {
            #     "firstName": record.get("First Name"),
            #     "lastName": record.get("Last Name"),
            #     "claims": [{"claimId": m["fields"].get("Claim ID"), 
            #                 "status": m["fields"].get("Claim Status")} for m in matches],
            #     "claimCount": len(matches)
            # }
        
        return None

    def log_interaction(self, caller_name: str, summary: str, sentiment: str):
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
        
        return self.interactions_table.create({
            "Caller Name": caller_name,
            "Call Summary": summary,
            "Sentiment": sentiment
        })

