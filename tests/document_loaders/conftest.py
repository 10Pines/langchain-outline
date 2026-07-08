from typing import Dict

import pytest

from langchain_outline.document_loaders.outline import OutlineLoader


@pytest.fixture
def outline_loader() -> OutlineLoader:
    return OutlineLoader(
        outline_base_url="http://outline.test", outline_api_key="test-api-key"
    )


@pytest.fixture
def mock_response_single_page() -> Dict:
    return {
        "data": [
            {
                "id": "1",
                "text": "Test document 1",
                "title": "Test 1",
                "createdAt": "2024-03-26T20:00:01.781Z",
                "updatedAt": "2024-03-26T20:00:01.781Z",
                "url": "/doc/test-RTYIxmoduo",
                "archivedAt": None,
                "deletedAt": None,
                "collectionId": "1899bf4d-98be-403a-baa2-ecc1e3361380",
                "parentDocumentId": None,
                "isCollectionDeleted": False,
            }
        ],
        "pagination": {
            "nextPath": "/api/documents.list?limit=25&offset=25",
            "total": 1,
        },
    }


@pytest.fixture
def mock_response_multiple_pages_page_1() -> Dict:
    return {
        "data": [
            {
                "id": "1",
                "text": "Test document 1",
                "title": "Test 1",
                "createdAt": "2024-03-26T20:00:01.781Z",
                "updatedAt": "2024-03-26T20:00:01.781Z",
                "url": "/doc/test-RTYIxmoduo",
                "archivedAt": None,
                "deletedAt": None,
                "collectionId": "1899bf4d-98be-403a-baa2-ecc1e3361380",
                "parentDocumentId": None,
                "isCollectionDeleted": False,
            }
        ],
        "pagination": {
            "nextPath": "/api/documents.list?limit=1&offset=1",
            "total": 2,
        },
    }


@pytest.fixture
def mock_response_multiple_pages_page_2() -> Dict:
    return {
        "data": [
            {
                "id": "2",
                "text": "Test document 2",
                "title": "Test 2",
                "createdAt": "2024-03-26T20:00:01.781Z",
                "updatedAt": "2024-03-26T20:00:01.781Z",
                "url": "/doc/test-RTYIxmodua",
                "archivedAt": None,
                "deletedAt": None,
                "collectionId": "1899bf4d-98be-403a-baa2-ecc1e3361380",
                "parentDocumentId": None,
                "isCollectionDeleted": False,
            }
        ],
        "pagination": {
            "nextPath": "http://outline.test/api/documents.list?limit=1&offset=2",
            "total": 2,
        },
    }

@pytest.fixture
def default_collection_item() -> Dict:
    return {
        "id": "1899bf4d-98be-403a-baa2-ecc1e3361380", # Matches collectionId in mock documents
        "name": "Default Test Collection",
        "description": "A default collection for testing.",
        "permission": "read",
        "url": "/collection/default-test-collection",
        "createdAt": "2024-01-01T00:00:00.000Z",
        "updatedAt": "2024-01-01T00:00:00.000Z",
    }

@pytest.fixture
def mock_response_collections_list_single_item(default_collection_item: Dict) -> Dict:
    return {
        "data": [default_collection_item],
        "pagination": {"nextPath": "/api/collections.list?limit=25&offset=25", "total": 1},
    }

@pytest.fixture
def doc_group_membership_item_for_doc1() -> Dict:
    # This is the object that _fetch_all is expected to yield for document "1"
    return {
        "groupMemberships": [
            {"id": "gm1", "groupId": "group1", "documentId": "1", "permission": "read"}
        ],
        "groups": [{"id": "group1", "name": "Test Group Alpha"}]
    }

@pytest.fixture
def mock_response_doc_group_memberships_for_doc1(doc_group_membership_item_for_doc1: Dict) -> Dict:
    # API response for /api/documents.group_memberships for document "1"
    return {
        "data": doc_group_membership_item_for_doc1,
        "pagination": {"total": 1, "nextPath": "/api/documents.group_memberships?limit=25&offset=25"}
    }

@pytest.fixture
def doc_group_membership_item_for_doc2() -> Dict:
    return {
        "groupMemberships": [
            {"id": "gm2", "groupId": "group2", "documentId": "2", "permission": "read_write"}
        ],
        "groups": [{"id": "group2", "name": "Test Group Beta"}]
    }

@pytest.fixture
def mock_response_doc_group_memberships_for_doc2(doc_group_membership_item_for_doc2: Dict) -> Dict:
    return {
        "data": doc_group_membership_item_for_doc2,
        "pagination": {"total": 1, "nextPath": "/api/documents.group_memberships?limit=25&offset=25"}
    }

@pytest.fixture
def specific_collection_item() -> Dict:
    return {
        "id": "SPECIFIC_COLLECTION_ID",
        "name": "Specific Collection Name",
        "description": "Specific Collection Description",
        "permission": "read_write",
        "url": "/collection/specific-coll-xyz",
        "createdAt": "2024-02-01T00:00:00.000Z",
        "updatedAt": "2024-02-01T00:00:00.000Z",
    }

@pytest.fixture
def doc_for_specific_collection(specific_collection_item: Dict) -> Dict:
    return {
        "id": "doc_specific_1", "text": "Document in specific collection", "title": "Specific Doc 1",
        "createdAt": "2024-03-27T20:00:01.781Z", "updatedAt": "2024-03-27T20:00:01.781Z",
        "url": "/doc/specific-doc-RTYIxmoduo", "archivedAt": None, "deletedAt": None,
        "collectionId": specific_collection_item["id"],
        "parentDocumentId": None, "isCollectionDeleted": False,
    }

@pytest.fixture
def mock_response_single_page_specific_collection(doc_for_specific_collection: Dict) -> Dict:
    return {"data": [doc_for_specific_collection], "pagination": {"total": 1, "nextPath": "http://outline.test/api/documents.list?limit=1&offset=2"}}

@pytest.fixture
def mock_response_collection_info(specific_collection_item: Dict) -> Dict:
    return { # Response for /api/collections.info
        "data": specific_collection_item
    }

@pytest.fixture
def mock_response_no_documents() -> Dict:
    return {"data": [], "pagination": {"total": 0, "offset": 0, "nextPath": None}}

@pytest.fixture
def mock_response_collections_list_multiple_items() -> Dict:
    return {
        "data": [
            {
                "id": "col1",
                "name": "Collection 1",
                "description": "First collection",
                "permission": "read",
            },
            {
                "id": "col2",
                "name": "Collection 2",
                "description": "Second collection",
                "permission": "read",
            },
        ],
        "pagination": {"nextPath": None, "total": 2},
    }
