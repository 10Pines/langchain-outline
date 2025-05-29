from typing import Dict

import pytest
import requests
import requests_mock

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

def test_fetch_single_page(
    outline_loader: OutlineLoader,
    mock_response_single_page: Dict,
    mock_response_collections_list_single_item: Dict,
    mock_response_doc_group_memberships_for_doc1: Dict,
) -> None:
    with requests_mock.Mocker() as m:
        m.post("http://outline.test/api/collections.list", json=mock_response_collections_list_single_item)
        m.post("http://outline.test/api/documents.list", json=mock_response_single_page)
        m.post("http://outline.test/api/documents.group_memberships", json=mock_response_doc_group_memberships_for_doc1)

        documents = outline_loader.load()

        assert len(documents) == 1
        assert documents[0].page_content == "Test document 1"


def test_fetch_multiple_pages(
    outline_loader: OutlineLoader,
    mock_response_multiple_pages_page_1: Dict,
    mock_response_multiple_pages_page_2: Dict,
    mock_response_collections_list_single_item: Dict,
    mock_response_doc_group_memberships_for_doc1: Dict,
    mock_response_doc_group_memberships_for_doc2: Dict,
) -> None:
    with requests_mock.Mocker() as m:
        m.post("http://outline.test/api/collections.list", json=mock_response_collections_list_single_item)
        m.post(
            "http://outline.test/api/documents.list",
            [
                {"json": mock_response_multiple_pages_page_1},
                {"json": mock_response_multiple_pages_page_2},
            ],
        )
        m.post(
            "http://outline.test/api/documents.group_memberships",
            [
                {"json": mock_response_doc_group_memberships_for_doc1}, # For doc "1"
                {"json": mock_response_doc_group_memberships_for_doc2}, # For doc "2"
            ],
        )
        documents = outline_loader.load()

        assert len(documents) == 2
        assert documents[0].page_content == "Test document 1"
        assert documents[1].page_content == "Test document 2"

def test_api_error_on_collections_list(outline_loader: OutlineLoader) -> None:
    with requests_mock.Mocker() as m:
        m.post("http://outline.test/api/collections.list", status_code=401)
        with pytest.raises(requests.exceptions.HTTPError):
            outline_loader.load()

def test_api_error_on_documents_list(
        outline_loader: OutlineLoader,
        mock_response_collections_list_single_item: Dict) -> None:
    with requests_mock.Mocker() as m:
        m.post("http://outline.test/api/collections.list", json=mock_response_collections_list_single_item) # Succeeds
        m.post("http://outline.test/api/documents.list", status_code=401)
        with pytest.raises(requests.exceptions.HTTPError):
            outline_loader.load()

def test_api_error_on_doc_group_memberships(
    outline_loader: OutlineLoader,
    mock_response_collections_list_single_item: Dict,
    mock_response_single_page: Dict, 
) -> None:
    with requests_mock.Mocker() as m:
        m.post("http://outline.test/api/collections.list", json=mock_response_collections_list_single_item)
        m.post("http://outline.test/api/documents.list", json=mock_response_single_page)
        m.post("http://outline.test/api/documents.group_memberships", status_code=401) # Fails
        with pytest.raises(requests.exceptions.HTTPError):
            outline_loader.load()

def test_document_metadata(
    outline_loader: OutlineLoader,
    mock_response_single_page: Dict,
    default_collection_item: Dict, 
    mock_response_collections_list_single_item: Dict,
    doc_group_membership_item_for_doc1: Dict,
    mock_response_doc_group_memberships_for_doc1: Dict,
) -> None:
    with requests_mock.Mocker() as m:
        m.post("http://outline.test/api/collections.list", json=mock_response_collections_list_single_item)
        m.post("http://outline.test/api/documents.list", json=mock_response_single_page)
        m.post("http://outline.test/api/documents.group_memberships", json=mock_response_doc_group_memberships_for_doc1)


        documents = outline_loader.load()

        assert len(documents) == 1
        document = documents[0]

        # Check that all metadata fields are present with correct values
        expected_source = "http://outline.test/doc/test-RTYIxmoduo"
        assert document.metadata["source"] == expected_source
        assert document.metadata["id"] == "1"
        assert document.metadata["title"] == "Test 1"
        assert document.metadata["createdAt"] == "2024-03-26T20:00:01.781Z"
        assert document.metadata["updatedAt"] == "2024-03-26T20:00:01.781Z"
        assert document.metadata["archivedAt"] == None
        assert document.metadata["isCollectionDeleted"] == False
        assert document.metadata["parentDocumentId"] == None
        assert document.metadata["collectionId"] == "1899bf4d-98be-403a-baa2-ecc1e3361380"
        assert document.metadata["deletedAt"] == None
        assert document.metadata["collection_permission"] == "read"
        assert document.metadata["collection_name"] == "Default Test Collection"
        assert document.metadata["collection_description"] == "A default collection for testing."
        assert document.metadata["read_groups"] == [{"id": "group1", "name": "Test Group Alpha"}]


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
def mock_response_collection_info(specific_collection_item: Dict) -> Dict:
    return { # Response for /api/collections.info
        "data": specific_collection_item
    }
def test_fetch_with_specific_collection_id(
    specific_collection_item: Dict,
    mock_response_collection_info: Dict, 
    mock_response_single_page_specific_collection: Dict,
    mock_response_doc_group_memberships_for_doc1: Dict,
) -> None:
    loader = OutlineLoader(
        outline_base_url="http://outline.test",
        outline_api_key="test-api-key",
        outline_collection_id_list=[specific_collection_item["id"]]
    )
    with requests_mock.Mocker() as m:
        m.post("http://outline.test/api/collections.info", json=mock_response_collection_info)
        m.post("http://outline.test/api/documents.list", json=mock_response_single_page_specific_collection)
        m.post("http://outline.test/api/documents.group_memberships", json=mock_response_doc_group_memberships_for_doc1)

        documents = loader.load()

        assert len(documents) == 1
        doc = documents[0]
        
        assert doc.page_content == "Document in specific collection"

def test_fetch_collection_info_api_error(
    specific_collection_item: Dict,
) -> None:
    loader = OutlineLoader(
        outline_base_url="http://outline.test",
        outline_api_key="test-api-key",
        outline_collection_id_list=[specific_collection_item["id"]]
    )
    with requests_mock.Mocker() as m:
        m.post("http://outline.test/api/collections.info", status_code=404) 

        with pytest.raises(requests.exceptions.HTTPError):
            loader.load()

@pytest.fixture
def mock_response_no_documents() -> Dict:
    return {"data": [], "pagination": {"total": 0, "offset": 0, "nextPath": None}}

def test_fetch_no_documents_in_collection(
    outline_loader: OutlineLoader,
    mock_response_collections_list_single_item: Dict,
    mock_response_no_documents: Dict,
) -> None:
    with requests_mock.Mocker() as m:
        m.post("http://outline.test/api/collections.list", json=mock_response_collections_list_single_item)
        m.post("http://outline.test/api/documents.list", json=mock_response_no_documents)
        
        documents = list(outline_loader.lazy_load()) 

        assert len(documents) == 0