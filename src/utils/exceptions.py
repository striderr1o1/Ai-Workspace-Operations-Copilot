class IngestionError(Exception):
    def __init__(self, text):
        self.text = text
        super().__init__(f"Error in Ingesting File: {text}")

class RetrievalError(Exception):
    def __init__(self, text):
        self.text = text
        super().__init__(f"Retrieval Error: {text}")

class AuthenticationError(Exception):
    """Carries the status code Supabase reported so routes can pass it through."""
    def __init__(self, text, status_code=400):
        self.text = text
        # 400 bad signup / 401 bad credentials / 429 rate limited / 500 our fault
        self.status_code = status_code
        super().__init__(f"Authentication Error: {text}")

