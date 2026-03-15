from ingestion import ingestion
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

ingestion_obj = ingestion('resume2-10.pdf', logging)
ingestion_obj.ingest_document()