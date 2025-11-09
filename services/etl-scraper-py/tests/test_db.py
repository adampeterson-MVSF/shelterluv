"""
Tests for database operations in db.py.
Critical functions: write_dogs, purge_stale_dogs, clear_all_dogs, get_db.
Tests batching logic, error handling, and data integrity.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import firebase_admin
from firebase_admin import firestore, credentials

from db import (
    get_db,
    write_dogs,
    purge_stale_dogs,
    clear_all_dogs,
    _chunk_operations,
    get_dog_collection,
    BATCH_SIZE
)


class TestChunkOperations:
    """Test the internal chunking utility."""

    def test_chunk_operations_empty_list(self):
        """Test chunking with empty list."""
        result = list(_chunk_operations([], 10))
        assert result == []

    def test_chunk_operations_single_chunk(self):
        """Test chunking when all items fit in one chunk."""
        items = [1, 2, 3, 4, 5]
        result = list(_chunk_operations(items, 10))
        assert result == [[1, 2, 3, 4, 5]]

    def test_chunk_operations_multiple_chunks(self):
        """Test chunking with multiple chunks."""
        items = [1, 2, 3, 4, 5, 6, 7]
        result = list(_chunk_operations(items, 3))
        assert result == [[1, 2, 3], [4, 5, 6], [7]]

    def test_chunk_operations_exact_chunks(self):
        """Test chunking with exact chunk size."""
        items = [1, 2, 3, 4, 5, 6]
        result = list(_chunk_operations(items, 3))
        assert result == [[1, 2, 3], [4, 5, 6]]


class TestWriteDogs:
    """Test write_dogs function - the most critical function for data integrity."""

    def test_write_dogs_empty_list(self):
        """Test write_dogs with empty list."""
        result = write_dogs([])
        assert result == {"dogs_written": 0, "batch_count": 0}

    def test_write_dogs_dry_run(self):
        """Test write_dogs dry run mode."""
        dogs = [
            {"Internal-ID": "1", "Name": "Dog1"},
            {"Internal-ID": "2", "Name": "Dog2"},
            {"Internal-ID": "3", "Name": "Dog3"},
        ]

        result = write_dogs(dogs, dry_run=True)
        assert result == {"dogs_written": 3, "batch_count": 1}

    def test_write_dogs_dry_run_large_batch(self):
        """Test write_dogs dry run with large batch requiring multiple chunks."""
        dogs = [{"Internal-ID": str(i), "Name": f"Dog{i}"} for i in range(BATCH_SIZE + 1)]

        result = write_dogs(dogs, dry_run=True)
        expected_batches = (len(dogs) + BATCH_SIZE - 1) // BATCH_SIZE
        assert result == {"dogs_written": len(dogs), "batch_count": expected_batches}

    @patch('db.get_db')
    def test_write_dogs_success_single_batch(self, mock_get_db):
        """Test successful write of dogs in single batch."""
        mock_db = Mock()
        mock_batch = Mock()
        mock_get_db.return_value = mock_db
        mock_db.batch.return_value = mock_batch
        mock_batch.commit.return_value = None

        dogs = [
            {"Internal-ID": "1", "Name": "Dog1"},
            {"Internal-ID": "2", "Name": "Dog2"},
        ]

        result = write_dogs(dogs)

        assert result == {"dogs_written": 2, "batch_count": 1}
        mock_db.batch.assert_called_once()
        assert mock_batch.set.call_count == 2
        mock_batch.commit.assert_called_once()

    @patch('db.get_db')
    def test_write_dogs_success_multiple_batches(self, mock_get_db):
        """Test successful write of dogs requiring multiple batches."""
        mock_db = Mock()
        mock_batch1 = Mock()
        mock_batch2 = Mock()
        mock_get_db.return_value = mock_db

        # Return different batch objects for different calls
        mock_db.batch.side_effect = [mock_batch1, mock_batch2]
        mock_batch1.commit.return_value = None
        mock_batch2.commit.return_value = None

        # Create enough dogs for 2 batches
        dogs = [{"Internal-ID": str(i), "Name": f"Dog{i}"} for i in range(BATCH_SIZE + 1)]

        result = write_dogs(dogs)

        assert result == {"dogs_written": len(dogs), "batch_count": 2}
        assert mock_db.batch.call_count == 2
        mock_batch1.commit.assert_called_once()
        mock_batch2.commit.assert_called_once()

    @patch('db.get_db')
    def test_write_dogs_missing_internal_id(self, mock_get_db):
        """Test write_dogs skips dogs without Internal-ID."""
        mock_db = Mock()
        mock_batch = Mock()
        mock_get_db.return_value = mock_db
        mock_db.batch.return_value = mock_batch
        mock_batch.commit.return_value = None

        dogs = [
            {"Internal-ID": "1", "Name": "Dog1"},
            {"Name": "DogWithoutID"},  # Missing Internal-ID
            {"Internal-ID": "3", "Name": "Dog3"},
        ]

        result = write_dogs(dogs)

        assert result == {"dogs_written": 2, "batch_count": 1}
        # Should only set 2 dogs (skipping the one without Internal-ID)
        assert mock_batch.set.call_count == 2


    @patch('db.get_db')
    def test_write_dogs_batch_commit_failure(self, mock_get_db):
        """Test write_dogs handles batch commit failures."""
        mock_db = Mock()
        mock_batch = Mock()
        mock_get_db.return_value = mock_db
        mock_db.batch.return_value = mock_batch
        mock_batch.commit.side_effect = Exception("Firestore error")

        dogs = [{"Internal-ID": "1", "Name": "Dog1"}]

        with pytest.raises(Exception, match="Firestore error"):
            write_dogs(dogs)

        # Should not return successful stats when batch fails
        # (This is implicit since exception is raised)

    @patch('db.datetime')
    @patch('db.get_db')
    def test_write_dogs_uses_correct_document_id(self, mock_get_db, mock_datetime):
        """Test write_dogs uses Internal-ID as document ID."""
        # Mock datetime to return a consistent timestamp
        mock_datetime.datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T12:00:00"

        mock_db = Mock()
        mock_batch = Mock()
        mock_collection = Mock()
        mock_doc = Mock()
        mock_get_db.return_value = mock_db
        mock_db.batch.return_value = mock_batch
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc
        mock_batch.commit.return_value = None

        dogs = [{"Internal-ID": "123", "Name": "Dog123"}]

        write_dogs(dogs)

        mock_db.collection.assert_called_with(get_dog_collection())
        mock_collection.document.assert_called_with("123")
        # Verify that metadata was added
        expected_dog = {"Internal-ID": "123", "Name": "Dog123", "metadata": {"etl_last_processed_at": "2023-01-01T12:00:00Z"}}
        mock_batch.set.assert_called_with(mock_doc, expected_dog, merge=True)


class TestPurgeStaleDogs:
    """Test purge_stale_dogs function - dangerous delete operation."""

    @patch('db.get_db')
    def test_purge_stale_dogs_dry_run(self, mock_get_db):
        """Test purge_stale_dogs dry run mode."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_docs = [
            Mock(id="1"),
            Mock(id="2"),
            Mock(id="3"),
        ]
        mock_get_db.return_value = mock_db
        mock_db.collection.return_value = mock_collection
        mock_collection.stream.return_value = mock_docs

        active_ids = {"1", "3"}
        result = purge_stale_dogs(active_ids, dry_run=True)

        assert result == 1  # Only dog "2" is stale
        mock_db.batch.assert_not_called()

    @patch('db.get_db')
    def test_purge_stale_dogs_no_stale_dogs(self, mock_get_db):
        """Test purge_stale_dogs when no dogs are stale."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_docs = [
            Mock(id="1"),
            Mock(id="2"),
        ]
        mock_get_db.return_value = mock_db
        mock_db.collection.return_value = mock_collection
        mock_collection.stream.return_value = mock_docs

        active_ids = {"1", "2"}
        result = purge_stale_dogs(active_ids)

        assert result == 0
        mock_db.batch.assert_not_called()

    @patch('db.get_db')
    def test_purge_stale_dogs_success(self, mock_get_db):
        """Test successful purge of stale dogs."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_batch = Mock()
        mock_docs = [
            Mock(id="1", reference=Mock()),
            Mock(id="2", reference=Mock()),
            Mock(id="3", reference=Mock()),
        ]
        mock_get_db.return_value = mock_db
        mock_db.collection.return_value = mock_collection
        mock_collection.stream.return_value = mock_docs
        mock_db.batch.return_value = mock_batch
        mock_batch.commit.return_value = None

        active_ids = {"1", "3"}  # Dog "2" is stale
        result = purge_stale_dogs(active_ids)

        assert result == 1
        mock_batch.delete.assert_called_once_with(mock_docs[1].reference)
        mock_batch.commit.assert_called_once()

    @patch('db.get_db')
    def test_purge_stale_dogs_multiple_batches(self, mock_get_db):
        """Test purge_stale_dogs with multiple batches."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_batch1 = Mock()
        mock_batch2 = Mock()

        # Create enough stale docs for 2 batches
        mock_docs = []
        for i in range(BATCH_SIZE + 1):
            mock_doc = Mock(id=str(i), reference=Mock())
            mock_docs.append(mock_doc)

        mock_get_db.return_value = mock_db
        mock_db.collection.return_value = mock_collection
        mock_collection.stream.return_value = mock_docs
        mock_db.batch.side_effect = [mock_batch1, mock_batch2]
        mock_batch1.commit.return_value = None
        mock_batch2.commit.return_value = None

        active_ids = set()  # All dogs are stale
        result = purge_stale_dogs(active_ids)

        assert result == len(mock_docs)
        assert mock_db.batch.call_count == 2
        mock_batch1.commit.assert_called_once()
        mock_batch2.commit.assert_called_once()

    @patch('db.get_db')
    def test_purge_stale_dogs_batch_commit_failure(self, mock_get_db):
        """Test purge_stale_dogs handles batch commit failures."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_batch = Mock()
        mock_docs = [
            Mock(id="1", reference=Mock()),
            Mock(id="2", reference=Mock()),
        ]
        mock_get_db.return_value = mock_db
        mock_db.collection.return_value = mock_collection
        mock_collection.stream.return_value = mock_docs
        mock_db.batch.return_value = mock_batch
        mock_batch.commit.side_effect = Exception("Delete failed")

        active_ids = set()  # All dogs are stale

        with pytest.raises(Exception, match="Delete failed"):
            purge_stale_dogs(active_ids)

        mock_batch.delete.assert_called()


class TestClearAllDogs:
    """Test clear_all_dogs function - nuclear option."""

    @patch('db.get_db')
    def test_clear_all_dogs_empty_collection(self, mock_get_db):
        """Test clear_all_dogs when collection is empty."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_get_db.return_value = mock_db
        mock_db.collection.return_value = mock_collection
        mock_collection.stream.return_value = []

        result = clear_all_dogs()

        assert result == 0
        mock_db.batch.assert_not_called()

    @patch('db.get_db')
    def test_clear_all_dogs_success(self, mock_get_db):
        """Test successful clear of all dogs."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_batch = Mock()
        mock_docs = [
            Mock(reference=Mock()),
            Mock(reference=Mock()),
            Mock(reference=Mock()),
        ]
        mock_get_db.return_value = mock_db
        mock_db.collection.return_value = mock_collection
        mock_collection.stream.return_value = mock_docs
        mock_db.batch.return_value = mock_batch
        mock_batch.commit.return_value = None

        result = clear_all_dogs()

        assert result == 3
        assert mock_batch.delete.call_count == 3
        mock_batch.commit.assert_called_once()

    @patch('db.get_db')
    def test_clear_all_dogs_multiple_batches(self, mock_get_db):
        """Test clear_all_dogs with multiple batches."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_batch1 = Mock()
        mock_batch2 = Mock()

        # Create enough docs for 2 batches
        mock_docs = []
        for i in range(BATCH_SIZE + 1):
            mock_doc = Mock(reference=Mock())
            mock_docs.append(mock_doc)

        mock_get_db.return_value = mock_db
        mock_db.collection.return_value = mock_collection
        mock_collection.stream.return_value = mock_docs
        mock_db.batch.side_effect = [mock_batch1, mock_batch2]
        mock_batch1.commit.return_value = None
        mock_batch2.commit.return_value = None

        result = clear_all_dogs()

        assert result == len(mock_docs)
        assert mock_db.batch.call_count == 2
        mock_batch1.commit.assert_called_once()
        mock_batch2.commit.assert_called_once()
