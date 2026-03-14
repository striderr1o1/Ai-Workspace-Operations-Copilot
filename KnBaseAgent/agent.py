#knowledge base agent class

from ingestion import ingestion

ingestion_obj = ingestion('../resume2-10.pdf')
ingestion_obj.ingest_document()