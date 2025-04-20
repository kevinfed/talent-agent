import hashlib
from openai import AsyncAzureOpenAI

async def get_hash(text: str):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

async def generate_embeddings(text: str, openai: AsyncAzureOpenAI):
        embedding = await openai.embeddings.create(
            model="text-embedding-ada-002",
            input=text,
            encoding_format="float"
        )
        return embedding.data[0].embedding