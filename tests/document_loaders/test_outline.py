from typing import Dict

import pytest
import requests
import requests_mock

from langchain_outline.document_loaders.outline import OutlineLoader


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

def test_fetch_no_documents_in_collection(
    outline_loader: OutlineLoader,
    mock_response_collections_list_single_item: Dict,
    mock_response_no_documents: Dict,
) -> None:
    with requests_mock.Mocker() as m:
        m.post("http://outline.test/api/collections.list", json=mock_response_collections_list_single_item)
        m.post("http://outline.test/api/documents.list", json=mock_response_no_documents)

        documents = list(outline_loader.lazy_load())

def test_continue_on_failure_collection_error(
    mock_response_collections_list_multiple_items: Dict,
    mock_response_single_page: Dict,
    mock_response_doc_group_memberships_for_doc1: Dict,
    caplog: pytest.LogCaptureFixture,
) -> None:
    loader = OutlineLoader(
        outline_base_url="http://outline.test",
        outline_api_key="test-api-key",
        continue_on_failure=True
    )
    with requests_mock.Mocker() as m:
        m.post("http://outline.test/api/collections.list", json=mock_response_collections_list_multiple_items)
        # Fail for col1, succeed for col2
        m.post("http://outline.test/api/documents.list", [
            {"status_code": 500},
            {"json": mock_response_single_page}
        ])
        m.post("http://outline.test/api/documents.group_memberships", json=mock_response_doc_group_memberships_for_doc1)

        documents = list(loader.lazy_load())

        assert len(documents) == 1
        assert documents[0].page_content == "Test document 1"
        assert "Error fetching documents for collection 'Collection 1'" in caplog.text

def test_continue_on_failure_group_memberships_error(
    mock_response_collections_list_single_item: Dict,
    mock_response_single_page: Dict,
    caplog: pytest.LogCaptureFixture,
) -> None:
    loader = OutlineLoader(
        outline_base_url="http://outline.test",
        outline_api_key="test-api-key",
        continue_on_failure=True
    )
    with requests_mock.Mocker() as m:
        m.post("http://outline.test/api/collections.list", json=mock_response_collections_list_single_item)
        m.post("http://outline.test/api/documents.list", json=mock_response_single_page)
        m.post("http://outline.test/api/documents.group_memberships", status_code=403)

        documents = list(loader.lazy_load())

        assert len(documents) == 1
        assert documents[0].metadata["read_groups"] == []
        assert "Could not fetch group permissions for document 'Test 1'" in caplog.text

def test_continue_on_failure_document_processing_error(
    mock_response_collections_list_single_item: Dict,
    caplog: pytest.LogCaptureFixture,
) -> None:
    loader = OutlineLoader(
        outline_base_url="http://outline.test",
        outline_api_key="test-api-key",
        continue_on_failure=True
    )
    # Document missing 'text' key will cause a KeyError in lazy_load
    bad_document_response = {
        "data": [
            {"id": "bad_doc", "title": "Bad Doc"}, # missing 'text'
            {"id": "good_doc", "text": "Good content", "title": "Good Doc", "url": "/good"}
        ],
        "pagination": {"total": 2, "nextPath": None}
    }
    with requests_mock.Mocker() as m:
        m.post("http://outline.test/api/collections.list", json=mock_response_collections_list_single_item)
        m.post("http://outline.test/api/documents.list", json=bad_document_response)
        # Mock _build_metadata stuff for the good doc
        m.post("http://outline.test/api/documents.group_memberships", json={"data": {"groups": []}, "pagination": {"total":0}})

        documents = list(loader.lazy_load())

        assert len(documents) == 1
        assert documents[0].page_content == "Good content"
        assert "Error processing document 'Bad Doc'" in caplog.text
