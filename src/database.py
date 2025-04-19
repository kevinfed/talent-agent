from __future__ import annotations

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator
from openai import AsyncAzureOpenAI
from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.cosmos import PartitionKey
from contextlib import asynccontextmanager
from utils import get_hash, generate_embeddings

@dataclass
class Database:
    client: CosmosClient
    db_name: str
    history_container_name: str
    cache_container_name: str

    @classmethod
    @asynccontextmanager
    async def connect(
        cls, url: str, credential: str, db_name: str, history_container_name: str, cache_container_name: str
    ) -> AsyncIterator[Database]:
        
        client = CosmosClient(url=url, credential=credential)
        try:
            db = await client.create_database_if_not_exists(id=db_name)

            history_container = await db.create_container_if_not_exists(
                id=history_container_name,
                partition_key=PartitionKey(path="/user_id"),
                offer_throughput=400,
                default_ttl=int(os.getenv("HISTORY_TTL", "10800"))
            )

            cache_container = await db.create_container_if_not_exists(
                id=cache_container_name,
                partition_key=PartitionKey(path="/query_hash"),
                offer_throughput=400,
                default_ttl=int(os.getenv("CACHE_TTL", "10800")),
                indexing_policy={
                    "indexingMode": "consistent",
                    "automatic": True,
                    "includedPaths": [{"path": "/*"}],
                    "excludedPaths": [{"path": "/queryVector/*"}],
                    "vectorIndexes": [
                        {
                            "path": "/queryVector",
                            "type": "quantizedFlat",
                            "dimensions": 1536,
                            "similarity": "cosine"
                        }
                    ]
                }
            )

            yield cls(client, db_name, history_container_name, cache_container_name)
        finally:
            await client.close()

    async def add_interaction(self, userId: str, query: str, response: str):
        try:
            history = await self.get_history(userId)
            userId = await get_hash(userId)
            container = self.client.get_database_client(self.db_name).get_container_client(self.history_container_name)

            qr_pair = {
                "User":query,
                "Sophie":response
            }
            history.append(qr_pair)
            # optional logic to trim message history
            if len(history) > 5:
                history = history[-5:]

            item_to_upsert = {
                "id": userId,
                "user_id": userId,
                "history": history
            }

            await container.upsert_item(item_to_upsert)
        except CosmosHttpResponseError as e:
            print(f"Error adding interaction: {e}")

    async def get_history(self, userId: str, n: int = None) -> list[dict]:
        try:
            userId = await get_hash(userId)
            container = self.client.get_database_client(self.db_name).get_container_client(self.history_container_name)
            query = f"SELECT * FROM c WHERE c.user_id = '{userId}'"
            items = [item async for item in container.query_items(query=query)]
            history = items[0].get("history", []) if items else []
            if n:
                return history[-n:]
            return history
        except CosmosHttpResponseError as e:
            print(f"Error retrieving history: {e}")
            return []
        
    async def search_cache(self, query: str, openai: AsyncAzureOpenAI) -> list[dict]:
        container = self.client.get_database_client(self.db_name).get_container_client(self.cache_container_name)
        query_hash = await get_hash(query)

        try:
            existing_item = await container.read_item(item=query_hash, partition_key=query_hash)
            new = dict(**existing_item)
            new['last_accessed'] = datetime.now().isoformat()
            await container.replace_item(item=existing_item, body=new)
            return existing_item.get("result")
        except:
            pass

        threshold = float(os.getenv("CACHE_SIMILARITY_THRESHOLD", "0.95"))
        query_embedding = await generate_embeddings(query, openai)

        query = """
        SELECT TOP 1 c.id, c.result, c.last_accessed, VectorDistance(c.embedding, @embedding) AS similarity
        FROM c 
        ORDER BY VectorDistance(c.embedding, @embedding)
        """

        params = [{"name": "@embedding", "value": query_embedding}]
        items = [item async for item in container.query_items(
                    query=query,
                    parameters=params
                )]
        
        if items:
            if items[0]['similarity'] < threshold:
                return None
            item_id = items[0]["id"]
            existing_item = await container.read_item(item=item_id, partition_key=item_id)
            new = dict(**existing_item)
            new['last_accessed'] = datetime.now().isoformat()
            await container.replace_item(item=existing_item,body=new)
            
            return items[0].get('result')

        return None

    async def update_cache(self, query: str, result: list[dict], openai: AsyncAzureOpenAI):
        container = self.client.get_database_client(self.db_name).get_container_client(self.cache_container_name)
        query_hash = await get_hash(query)
        query_embedding = await generate_embeddings(query, openai)

        try:
            query_count = len([item async for item in container.query_items(
                query="SELECT VALUE COUNT(1) FROM c"
            )])

            cache_max_size = int(os.getenv("CACHE_MAX_SIZE", "1000"))
            if query_count >= cache_max_size:
                eviction_query = """
                SELECT TOP 1 c.id 
                FROM c 
                ORDER BY c.last_accessed ASC
                """
                items_to_evict = [item async for item in container.query_items(
                    query=eviction_query
                )]

                if items_to_evict:
                    await container.delete_item(
                        item=items_to_evict[0],
                        partition_key=items_to_evict[0]['id']
                    )

            cache_item = {
                'id': query_hash,
                'query_hash': query_hash,
                'query': query,
                'result': result,
                'embedding': query_embedding,
                'last_accessed': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat()
            }
            await container.upsert_item(body=cache_item)

        except Exception as e:
            print(f"Cache update error: {e}")