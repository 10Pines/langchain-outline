import asyncio
import time
from typing import Dict, List

import httpx
import pytest
import respx

from langchain_outline.document_loaders.outline import OutlineLoader


@respx.mock
async def test_afetch_single_page(
    outline_loader: OutlineLoader,
    mock_response_single_page: Dict,
    mock_response_collections_list_single_item: Dict,
    mock_response_doc_group_memberships_for_doc1: Dict,
) -> None:
    respx.post("http://outline.test/api/collections.list").mock(
        return_value=httpx.Response(200, json=mock_response_collections_list_single_item)
    )
    respx.post("http://outline.test/api/documents.list").mock(
        return_value=httpx.Response(200, json=mock_response_single_page)
    )
    respx.post("http://outline.test/api/documents.group_memberships").mock(
        return_value=httpx.Response(200, json=mock_response_doc_group_memberships_for_doc1)
    )

    documents = await outline_loader.aload()

    assert len(documents) == 1
    assert documents[0].page_content == "Test document 1"


@respx.mock
async def test_afetch_multiple_pages(
    outline_loader: OutlineLoader,
    mock_response_multiple_pages_page_1: Dict,
    mock_response_multiple_pages_page_2: Dict,
    mock_response_collections_list_single_item: Dict,
    mock_response_doc_group_memberships_for_doc1: Dict,
    mock_response_doc_group_memberships_for_doc2: Dict,
) -> None:
    respx.post("http://outline.test/api/collections.list").mock(
        return_value=httpx.Response(200, json=mock_response_collections_list_single_item)
    )
    respx.post("http://outline.test/api/documents.list").mock(
        side_effect=[
            httpx.Response(200, json=mock_response_multiple_pages_page_1),
            httpx.Response(200, json=mock_response_multiple_pages_page_2),
        ]
    )
    respx.post("http://outline.test/api/documents.group_memberships").mock(
        side_effect=[
            httpx.Response(200, json=mock_response_doc_group_memberships_for_doc1),
            httpx.Response(200, json=mock_response_doc_group_memberships_for_doc2),
        ]
    )

    documents = await outline_loader.aload()

    assert len(documents) == 2
    assert documents[0].page_content == "Test document 1"
    assert documents[1].page_content == "Test document 2"


@respx.mock
async def test_aapi_error_on_collections_list(outline_loader: OutlineLoader) -> None:
    respx.post("http://outline.test/api/collections.list").mock(return_value=httpx.Response(401))
    with pytest.raises(httpx.HTTPStatusError):
        await outline_loader.aload()


@respx.mock
async def test_aapi_error_on_documents_list(
    outline_loader: OutlineLoader,
    mock_response_collections_list_single_item: Dict,
) -> None:
    respx.post("http://outline.test/api/collections.list").mock(
        return_value=httpx.Response(200, json=mock_response_collections_list_single_item)
    )
    respx.post("http://outline.test/api/documents.list").mock(return_value=httpx.Response(401))
    with pytest.raises(httpx.HTTPStatusError):
        await outline_loader.aload()


@respx.mock
async def test_aapi_error_on_doc_group_memberships(
    outline_loader: OutlineLoader,
    mock_response_collections_list_single_item: Dict,
    mock_response_single_page: Dict,
) -> None:
    respx.post("http://outline.test/api/collections.list").mock(
        return_value=httpx.Response(200, json=mock_response_collections_list_single_item)
    )
    respx.post("http://outline.test/api/documents.list").mock(
        return_value=httpx.Response(200, json=mock_response_single_page)
    )
    respx.post("http://outline.test/api/documents.group_memberships").mock(return_value=httpx.Response(401))
    with pytest.raises(httpx.HTTPStatusError):
        await outline_loader.aload()


@respx.mock
async def test_adocument_metadata(
    outline_loader: OutlineLoader,
    mock_response_single_page: Dict,
    default_collection_item: Dict,
    mock_response_collections_list_single_item: Dict,
    doc_group_membership_item_for_doc1: Dict,
    mock_response_doc_group_memberships_for_doc1: Dict,
) -> None:
    respx.post("http://outline.test/api/collections.list").mock(
        return_value=httpx.Response(200, json=mock_response_collections_list_single_item)
    )
    respx.post("http://outline.test/api/documents.list").mock(
        return_value=httpx.Response(200, json=mock_response_single_page)
    )
    respx.post("http://outline.test/api/documents.group_memberships").mock(
        return_value=httpx.Response(200, json=mock_response_doc_group_memberships_for_doc1)
    )

    documents = await outline_loader.aload()

    assert len(documents) == 1
    document = documents[0]

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


@respx.mock
async def test_afetch_with_specific_collection_id(
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
    respx.post("http://outline.test/api/collections.info").mock(
        return_value=httpx.Response(200, json=mock_response_collection_info)
    )
    respx.post("http://outline.test/api/documents.list").mock(
        return_value=httpx.Response(200, json=mock_response_single_page_specific_collection)
    )
    respx.post("http://outline.test/api/documents.group_memberships").mock(
        return_value=httpx.Response(200, json=mock_response_doc_group_memberships_for_doc1)
    )

    documents = await loader.aload()

    assert len(documents) == 1
    assert documents[0].page_content == "Document in specific collection"


@respx.mock
async def test_afetch_collection_info_api_error(
    specific_collection_item: Dict,
) -> None:
    loader = OutlineLoader(
        outline_base_url="http://outline.test",
        outline_api_key="test-api-key",
        outline_collection_id_list=[specific_collection_item["id"]]
    )
    respx.post("http://outline.test/api/collections.info").mock(return_value=httpx.Response(404))

    with pytest.raises(httpx.HTTPStatusError):
        await loader.aload()


@respx.mock
async def test_afetch_no_documents_in_collection(
    outline_loader: OutlineLoader,
    mock_response_collections_list_single_item: Dict,
    mock_response_no_documents: Dict,
) -> None:
    respx.post("http://outline.test/api/collections.list").mock(
        return_value=httpx.Response(200, json=mock_response_collections_list_single_item)
    )
    respx.post("http://outline.test/api/documents.list").mock(
        return_value=httpx.Response(200, json=mock_response_no_documents)
    )

    documents = [doc async for doc in outline_loader.alazy_load()]

    assert documents == []


@respx.mock
async def test_acontinue_on_failure_collection_error(
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
    respx.post("http://outline.test/api/collections.list").mock(
        return_value=httpx.Response(200, json=mock_response_collections_list_multiple_items)
    )
    # Fail for col1, succeed for col2
    respx.post("http://outline.test/api/documents.list").mock(
        side_effect=[
            httpx.Response(500),
            httpx.Response(200, json=mock_response_single_page),
        ]
    )
    respx.post("http://outline.test/api/documents.group_memberships").mock(
        return_value=httpx.Response(200, json=mock_response_doc_group_memberships_for_doc1)
    )

    documents = [doc async for doc in loader.alazy_load()]

    assert len(documents) == 1
    assert documents[0].page_content == "Test document 1"
    assert "Error fetching documents for collection 'Collection 1'" in caplog.text


@respx.mock
async def test_acontinue_on_failure_group_memberships_error(
    mock_response_collections_list_single_item: Dict,
    mock_response_single_page: Dict,
    caplog: pytest.LogCaptureFixture,
) -> None:
    loader = OutlineLoader(
        outline_base_url="http://outline.test",
        outline_api_key="test-api-key",
        continue_on_failure=True
    )
    respx.post("http://outline.test/api/collections.list").mock(
        return_value=httpx.Response(200, json=mock_response_collections_list_single_item)
    )
    respx.post("http://outline.test/api/documents.list").mock(
        return_value=httpx.Response(200, json=mock_response_single_page)
    )
    respx.post("http://outline.test/api/documents.group_memberships").mock(return_value=httpx.Response(403))

    documents = [doc async for doc in loader.alazy_load()]

    assert len(documents) == 1
    assert documents[0].metadata["read_groups"] == []
    assert "Could not fetch group permissions for document 'Test 1'" in caplog.text


@respx.mock
async def test_acontinue_on_failure_document_processing_error(
    mock_response_collections_list_single_item: Dict,
    caplog: pytest.LogCaptureFixture,
) -> None:
    loader = OutlineLoader(
        outline_base_url="http://outline.test",
        outline_api_key="test-api-key",
        continue_on_failure=True
    )
    # Document missing 'text' key will cause a KeyError in alazy_load
    bad_document_response = {
        "data": [
            {"id": "bad_doc", "title": "Bad Doc"}, # missing 'text'
            {"id": "good_doc", "text": "Good content", "title": "Good Doc", "url": "/good"}
        ],
        "pagination": {"total": 2, "nextPath": None}
    }
    respx.post("http://outline.test/api/collections.list").mock(
        return_value=httpx.Response(200, json=mock_response_collections_list_single_item)
    )
    respx.post("http://outline.test/api/documents.list").mock(
        return_value=httpx.Response(200, json=bad_document_response)
    )
    respx.post("http://outline.test/api/documents.group_memberships").mock(
        return_value=httpx.Response(200, json={"data": {"groups": []}, "pagination": {"total": 0}})
    )

    documents = [doc async for doc in loader.alazy_load()]

    assert len(documents) == 1
    assert documents[0].page_content == "Good content"
    assert "Error processing document 'Bad Doc'" in caplog.text


@respx.mock
async def test_alazy_load_is_non_blocking(
    mock_response_collections_list_single_item: Dict,
    mock_response_single_page: Dict,
    mock_response_doc_group_memberships_for_doc1: Dict,
) -> None:
    """Proves alazy_load performs real async I/O rather than sequentially blocking:
    two independent full consumptions run concurrently in less than the sum of
    their individual artificial response delays."""
    delay_seconds = 0.2

    async def slow_documents_response(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(delay_seconds)
        return httpx.Response(200, json=mock_response_single_page)

    respx.post("http://outline.test/api/collections.list").mock(
        return_value=httpx.Response(200, json=mock_response_collections_list_single_item)
    )
    respx.post("http://outline.test/api/documents.list").mock(side_effect=slow_documents_response)
    respx.post("http://outline.test/api/documents.group_memberships").mock(
        return_value=httpx.Response(200, json=mock_response_doc_group_memberships_for_doc1)
    )

    loader_1 = OutlineLoader(outline_base_url="http://outline.test", outline_api_key="test-api-key")
    loader_2 = OutlineLoader(outline_base_url="http://outline.test", outline_api_key="test-api-key")

    start = time.monotonic()
    results: List[List] = await asyncio.gather(loader_1.aload(), loader_2.aload())
    elapsed = time.monotonic() - start

    assert all(len(docs) == 1 for docs in results)
    assert elapsed < delay_seconds * 1.75
