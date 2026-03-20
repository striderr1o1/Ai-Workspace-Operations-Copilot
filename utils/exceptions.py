class IngestionError(Exception):
    def __init__(self, text):
        self.text = text
        super().__init__(f"Error in Ingesting File: {text}")

class RetrievalError(Exception):
    def __init__(self, text):
        self.text = text
        super().__init__(f"Retrieval Error: {text}")