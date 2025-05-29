import os
from typing import Any, Callable, Dict, Iterable, Iterator, List, Tuple, Union

import requests
from langchain_core.documents import Document

from langchain_community.document_loaders.base import BaseLoader

class OutlineLoader(BaseLoader):
    """Load `Outline` documents.

    This loader will use the Outline API to retrieve all documents in an Outline
    instance.  You will need the API key from Outline to configure the loader.
    The API used is documented here: https://www.getoutline.com/developers

    If not passed in as parameters the API key and will be taken from env
    vars OUTLINE_INSTANCE_URL and OUTLINE_API_KEY.

    Examples
    --------
    from langchain_community.document_loaders import OutlineLoader

    loader = OutlineLoader(
        outline_base_url="outlinewiki.somedomain.com", outline_api_key="theapikey"
    )
    docs = loader.load()
    """

    @staticmethod
    def no_transform(entries: Iterable) -> Iterable:
        return entries

    def __init__(
        self,
        outline_base_url: Union[str | None] = None,
        outline_api_key: Union[str | None] = None,
        outline_collection_id_list: Union[List[str] | None] = None,
        page_size: int = 25,
    ):
        """Initialize with url, api_key and requested page size for API results
        pagination.

        :param outline_base_url: The URL of the outline instance.

        :param outline_api_key: API key for accessing the outline instance.

        :param outline_collection_id_list: List of collection ids to be retrieved. If None all will be retrieved.

        :param page_size: How many outline documents should be retrieved per request
        """

        self.outline_base_url = outline_base_url or os.environ["OUTLINE_INSTANCE_URL"]
        self.outline_api_key = outline_api_key or os.environ["OUTLINE_API_KEY"]
        self.document_list_endpoint = f"{self.outline_base_url}/api/documents.list"
        self.document_group_membership_endpoint = f"{self.outline_base_url}/api/documents.group_memberships"
        self.collection_list_endpoint = f"{self.outline_base_url}/api/collections.list"
        self.collection_info_endpoint = f"{self.outline_base_url}/api/collections.info"
        self.collection_ids = outline_collection_id_list
        self.page_size = page_size
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {outline_api_key}",
        }

    def lazy_load(self) -> Iterator[Document]:
        """
        Loads documents from Outline.
        """
        for collection in self._collections():
            documents = self._fetch_documents(collection["id"])
            for document in documents:
                text = document["text"]
                metadata = self._build_metadata(document, collection)
                yield Document(page_content=text, metadata=metadata)

    def _build_metadata(self, document: Any, collection: Any) -> Dict:
        document_group_permission_metadata = self._fetch_document_group_permission_metadata(document["id"])
        read_groups = []
        for document_group_permission in document_group_permission_metadata:
            read_groups.extend(document_group_permission["groups"])
        metadata = {"source": f"{self.outline_base_url}{document['url']}"}
        metadata["collection_permission"] = collection["permission"]
        metadata["collection_name"] = collection["name"]
        metadata["collection_description"] = collection["description"]
        metadata["read_groups"] = read_groups
        metadata_keys = ["id", "title", "createdAt", "updatedAt", "deletedAt", "archivedAt", "isCollectionDeleted", "parentDocumentId", "collectionId"]
        for key in metadata_keys:
            metadata[key] = document.get(key)
        return metadata
    
    def _fetch_document_group_permission_metadata(self, document_id:str) -> Iterator[Dict]:
        query = { "id": document_id }
        yield from self._fetch_all(self.document_group_membership_endpoint, query, lambda dic: [dic])
    
    def _collections(self) ->  Iterator[Dict]:
        if self.collection_ids:
            for collection_id in self.collection_ids:
                yield self._fetch_collection(collection_id)
        else:
            yield from self._fetch_all_collections()
    
    def _fetch_collection(self, collection_id:str) -> Iterator[Dict]:
        response = requests.post(
            self.collection_info_endpoint, json={"id": collection_id}, headers=self.headers
        )
        response.raise_for_status()
        response_json = response.json()
        return response_json["data"]
    
    def _fetch_all_collections(self) -> Iterator[Dict]:
        return self._fetch_all(self.collection_list_endpoint)
    
    def _fetch_documents(self, collection_id: str) -> Iterator[Dict]:
        query = { "collectionId": collection_id }
        return self._fetch_all(self.document_list_endpoint, query)

    def _fetch_all(self, endpoint: str, query: Union[Dict[str, str] | None] = None, entries_adapter: Callable = no_transform) -> Iterator[Dict]:
        starting_offset = 0

        offset, total, page_entries = self._fetch_page(endpoint, starting_offset, query)
        yield from entries_adapter(page_entries)

        while offset < total:
            offset, _, page_entries = self._fetch_page(endpoint, offset, query)
            yield from entries_adapter(page_entries)

    def _fetch_page(self, endpoint: str, offset: int, query: Union[Dict[str, str] | None] = None) -> Tuple[int, int, List[Dict]]:
        payload = {
            "offset": offset,
            "limit": self.page_size,
            "sort": "updatedAt",
            "direction": "DESC",
        }
        if query:
            payload.update(query)
        response = requests.post(
            endpoint, json=payload, headers=self.headers
        )
        response.raise_for_status()
        response_json = response.json()
        offset, total_documents = self._extract_pagination_info(
            response_json["pagination"]
        )
        return offset, total_documents, response_json["data"]

    def _extract_pagination_info(self, pagination_data: Dict) -> Tuple[int, int]:
        next_path = pagination_data.get("nextPath", "")
        next_offset = 0
        if next_path:
            try:
                offset_str = next_path.split("offset=")[1].split("&")[0]
                next_offset = int(offset_str)
            except (IndexError, ValueError):
                next_offset = 0

        total = pagination_data.get("total", 0)

        return next_offset, total