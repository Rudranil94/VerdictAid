from typing import List, Dict, Optional
from elasticsearch import AsyncElasticsearch
from app.core.config import settings
from app.core.cache import cache
from datetime import datetime
import asyncio

class SearchService:
    def __init__(self):
        self.es = AsyncElasticsearch([settings.ELASTICSEARCH_URL])
        self.index_name = "verdict_aid_documents"
        self.index_settings = {
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 1,
                "analysis": {
                    "analyzer": {
                        "ngram_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "ngram_filter"]
                        }
                    },
                    "filter": {
                        "ngram_filter": {
                            "type": "ngram",
                            "min_gram": 2,
                            "max_gram": 20
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "content": {
                        "type": "text",
                        "analyzer": "standard",
                        "search_analyzer": "standard",
                        "fields": {
                            "ngram": {
                                "type": "text",
                                "analyzer": "ngram_analyzer"
                            }
                        }
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "text"},
                            "document_type": {"type": "keyword"},
                            "language": {"type": "keyword"},
                            "tags": {"type": "keyword"},
                            "created_at": {"type": "date"},
                            "updated_at": {"type": "date"},
                            "access_control": {
                                "type": "object",
                                "properties": {
                                    "user_id": {"type": "keyword"},
                                    "organization_id": {"type": "keyword"},
                                    "permissions": {"type": "keyword"}
                                }
                            }
                        }
                    },
                    "vector_embedding": {
                        "type": "dense_vector",
                        "dims": 768  # BERT embedding dimension
                    }
                }
            }
        }
    
    async def initialize_index(self):
        """Initialize Elasticsearch index with settings and mappings."""
        if not await self.es.indices.exists(index=self.index_name):
            await self.es.indices.create(
                index=self.index_name,
                body=self.index_settings
            )
    
    @cache(expire=300)
    async def search_documents(
        self,
        query: str,
        filters: Optional[Dict] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Dict:
        """Enhanced document search with advanced features."""
        search_query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [
                                    "content^2",
                                    "content.ngram",
                                    "metadata.title^3",
                                    "metadata.tags^1.5"
                                ],
                                "type": "best_fields",
                                "fuzziness": "AUTO",
                                "minimum_should_match": "75%"
                            }
                        }
                    ],
                    "should": [
                        {
                            "match_phrase": {
                                "content": {
                                    "query": query,
                                    "boost": 2,
                                    "slop": 2
                                }
                            }
                        }
                    ]
                }
            },
            "highlight": {
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"],
                "fields": {
                    "content": {
                        "fragment_size": 150,
                        "number_of_fragments": 3,
                        "type": "unified"
                    },
                    "metadata.title": {},
                    "metadata.tags": {}
                }
            },
            "aggs": {
                "document_types": {
                    "terms": {"field": "metadata.document_type"}
                },
                "languages": {
                    "terms": {"field": "metadata.language"}
                },
                "tags": {
                    "terms": {"field": "metadata.tags"}
                }
            }
        }
        
        # Add filters
        if filters:
            filter_clauses = []
            for key, value in filters.items():
                if key == "date_range":
                    filter_clauses.append({
                        "range": {
                            "metadata.created_at": value
                        }
                    })
                elif key == "access_control":
                    filter_clauses.append({
                        "bool": {
                            "should": [
                                {"term": {"metadata.access_control.user_id": value["user_id"]}},
                                {"term": {"metadata.access_control.organization_id": value["organization_id"]}}
                            ]
                        }
                    })
                else:
                    filter_clauses.append({"term": {f"metadata.{key}": value}})
            
            search_query["query"]["bool"]["filter"] = filter_clauses
        
        # Add pagination
        from_idx = (page - 1) * page_size
        search_query["from"] = from_idx
        search_query["size"] = page_size
        
        # Execute search
        response = await self.es.search(
            index=self.index_name,
            body=search_query
        )
        
        # Process results
        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]
        aggregations = response["aggregations"]
        
        results = []
        for hit in hits:
            result = {
                "document_id": hit["_source"]["document_id"],
                "score": hit["_score"],
                "metadata": hit["_source"]["metadata"],
                "highlights": hit.get("highlight", {}),
                "content_preview": hit["_source"]["content"][:200] + "..."
            }
            results.append(result)
        
        return {
            "results": results,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "aggregations": aggregations
        }
    
    async def get_suggestions(
        self,
        query: str,
        field: str
    ) -> List[Dict]:
        """Get search suggestions for autocomplete."""
        suggest_query = {
            "suggest": {
                "text": query,
                f"{field}_suggest": {
                    "completion": {
                        "field": f"metadata.{field}_suggest",
                        "skip_duplicates": True,
                        "size": 5
                    }
                }
            }
        }
        
        response = await self.es.search(
            index=self.index_name,
            body=suggest_query
        )
        
        return response["suggest"][f"{field}_suggest"][0]["options"]
    
    async def reindex_all_documents(self):
        """Rebuild the entire search index."""
        # Create new index with updated settings
        temp_index = f"{self.index_name}_new"
        await self.es.indices.create(
            index=temp_index,
            body=self.index_settings
        )
        
        # Reindex documents
        await self.es.reindex(
            body={
                "source": {"index": self.index_name},
                "dest": {"index": temp_index}
            }
        )
        
        # Swap indices
        await self.es.indices.delete(index=self.index_name)
        await self.es.indices.put_alias(
            index=temp_index,
            name=self.index_name
        )
        
        return {"status": "completed"}

search_service = SearchService()
