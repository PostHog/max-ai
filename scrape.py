from pipeline import MaxPipeline
from dotenv import load_dotenv

import os
from ai import ai_response

load_dotenv()

pipeline = MaxPipeline(
    openai_token=os.getenv("OPENAI_TOKEN")
)

# Scrape and embed
# pipeline.embed_from_url(urls=["https://keajs.org/docs/intro/what-is-kea"])
# pipeline.update_embeddings()


# Example usage
print(ai_response("What is a selector in kea?", "kea"))
