import firebase_admin
from firebase_admin import firestore, credentials
from typing import List, Dict, Any, Set
import logging
import os
import datetime

logger = logging.getLogger(__name__)

# Use configurable collection name, defaulting to "dogs"
BATCH_SIZE = 500

def get_dog_collection():
    """Get the dog collection name, allowing tests to override via environment."""
    return os.environ.get("DOGS_COLLECTION", "dogs")

# DOG_COLLECTION is now dynamic - use get_dog_collection() instead

def get_db():
    """
    Get Firestore client using service account credentials.
    """
    # Check if we're running against the emulator
    emulator_host = os.environ.get('FIRESTORE_EMULATOR_HOST')

    if emulator_host:
        try:
            # Try to use existing app
            return firestore.client()
        except ValueError:
            # Delete any existing apps to start fresh
            for app in firebase_admin._apps.copy().values():
                firebase_admin.delete_app(app)
            # Use emulator - no credentials needed, but must set credential=None
            firebase_admin.initialize_app(credential=None, options={
                'projectId': 'demo-project',  # Dummy project ID for emulator
            })
            logger.info(f"Initialized Firebase app for emulator at {emulator_host}")
            return firestore.client()
    else:
        # Production mode - use service account
        try:
            # Try to use existing app
            return firestore.client()
        except ValueError:
            # Initialize new app with service account credentials
            # Look for service account key in the project root
            service_account_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'firebase-admin-key.json')
            if os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred, {
                    'projectId': 'muttville'
                })
                logger.info("Initialized Firebase app with service account credentials")
            else:
                # Fallback to default credentials if service account key not found
                firebase_admin.initialize_app()
                logger.info("Initialized Firebase app with default credentials (service account key not found)")
            return firestore.client()

def _chunk_operations(operations: List, chunk_size: int):
    """Chunk operations into batches."""
    for i in range(0, len(operations), chunk_size):
        yield operations[i:i + chunk_size]

def write_dogs(dogs_data: List[Dict[str, Any]], dry_run: bool = False) -> Dict[str, int]:
    """
    Write dogs to Firestore in batched chunks.
    Returns stats dict with dogs_written, batch_count.
    Enforces Internal-ID consistency: Firestore doc ID must equal dog["Internal-ID"].
    """
    if not dogs_data:
        return {"dogs_written": 0, "batch_count": 0}

    if dry_run:
        logger.info(f"Dry run: would write {len(dogs_data)} dogs")
        return {"dogs_written": len(dogs_data), "batch_count": (len(dogs_data) + BATCH_SIZE - 1) // BATCH_SIZE}

    db = get_db()
    written_count = 0
    batch_count = 0

    # Execute in chunks with error handling for partial failures
    for chunk in _chunk_operations(dogs_data, BATCH_SIZE):
        batch = db.batch()
        chunk_written = 0

        for dog in chunk:
            internal_id = dog.get("Internal-ID")
            if not internal_id:
                continue

            # Enforce Internal-ID consistency
            doc_id = str(internal_id)
            if doc_id != str(dog["Internal-ID"]):
                raise ValueError(f"Internal-ID mismatch: doc_id={doc_id}, dog.Internal-ID={dog['Internal-ID']}")

            # Add ETL metadata to the dog record
            source_updated_at = dog.get("SourceUpdatedAt")
            dog_with_metadata = _add_etl_metadata(dog, source_updated_at)

            doc_ref = db.collection(get_dog_collection()).document(doc_id)
            batch.set(doc_ref, dog_with_metadata, merge=True)
            chunk_written += 1

        if chunk_written > 0:
            try:
                logger.info(f"Committing batch with {chunk_written} dogs to collection {get_dog_collection()}")
                result = batch.commit()
                logger.info(f"Batch commit result: {result}")
                written_count += chunk_written
                batch_count += 1
                logger.info(f"Successfully committed batch {batch_count}, total written so far: {written_count}")
            except Exception as e:
                logger.error(f"Failed to write batch of {chunk_written} dogs: {e}")
                logger.error(f"Exception type: {type(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Don't increment counts for failed batch
                raise

    logger.info(f"Wrote {written_count} dogs in {batch_count} batches")
    return {"dogs_written": written_count, "batch_count": batch_count}

def purge_stale_dogs(active_dog_ids: Set[str], dry_run: bool = False) -> int:
    """
    Delete dogs not in active_dog_ids.
    Returns number of dogs that would be deleted (or were deleted if not dry_run).
    """
    if dry_run:
        db = get_db()
        docs = list(db.collection(get_dog_collection()).stream())
        stale_count = len([doc for doc in docs if doc.id not in active_dog_ids])
        logger.info(f"Dry run: would purge {stale_count} stale dogs")
        return stale_count

    db = get_db()
    deleted_count = 0

    # Get all existing docs
    docs = list(db.collection(get_dog_collection()).stream())

    # Execute in chunks with error handling
    stale_doc_refs = [doc.reference for doc in docs if doc.id not in active_dog_ids]
    for chunk in _chunk_operations(stale_doc_refs, BATCH_SIZE):
        batch = db.batch()
        for ref in chunk:
            batch.delete(ref)

        if chunk:  # Only commit if there are operations in the batch
            try:
                batch.commit()
                deleted_count += len(chunk)
            except Exception as e:
                logger.error(f"Failed to delete batch of {len(chunk)} stale dogs: {e}")
                raise

    logger.info(f"Purged {deleted_count} stale dogs")
    return deleted_count

def clear_all_dogs() -> int:
    """
    Clear ALL documents from the dogs collection.
    Returns number of dogs deleted.
    """
    db = get_db()
    deleted_count = 0

    # Get all existing docs
    docs = list(db.collection(get_dog_collection()).stream())

    if not docs:
        logger.info("No dogs found to delete")
        return 0

    # Execute in chunks
    doc_refs = [doc.reference for doc in docs]
    for chunk in _chunk_operations(doc_refs, BATCH_SIZE):
        batch = db.batch()
        for ref in chunk:
            batch.delete(ref)
        batch.commit()
        deleted_count += len(chunk)

    logger.info(f"Cleared {deleted_count} dogs from database")
    return deleted_count

def fetch_existing_metadata(internal_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetch existing metadata for dogs by internal IDs.
    Returns dict mapping internal_id to metadata dict.

    Metadata includes:
    - source_updated_at: Last ShelterLuv update timestamp seen
    - etl_last_processed_at: Last time ETL processed this dog
    """
    if not internal_ids:
        return {}

    db = get_db()
    metadata = {}

    # Firestore doesn't support "in" queries on document IDs, so we need to fetch each doc individually
    # In practice, this should be fine since we're dealing with incremental updates
    for internal_id in internal_ids:
        try:
            doc = db.collection(get_dog_collection()).document(str(internal_id)).get()
            if doc.exists:
                data = doc.to_dict()
                metadata[str(internal_id)] = {
                    "source_updated_at": data.get("metadata", {}).get("source_updated_at", ""),
                    "etl_last_processed_at": data.get("metadata", {}).get("etl_last_processed_at", ""),
                }
        except Exception as e:
            logger.warning(f"Failed to fetch metadata for dog {internal_id}: {e}")
            # Continue with other dogs rather than failing the whole batch

    return metadata

def _add_etl_metadata(dog: Dict[str, Any], source_updated_at: str = None) -> Dict[str, Any]:
    """
    Add ETL metadata to a dog record.
    Updates etl_last_processed_at and optionally source_updated_at.
    """
    result = dict(dog)
    metadata = result.get("metadata", {})

    # Always update the ETL processing timestamp
    metadata["etl_last_processed_at"] = datetime.datetime.utcnow().isoformat() + "Z"

    # Update source timestamp if provided
    if source_updated_at:
        metadata["source_updated_at"] = source_updated_at

    result["metadata"] = metadata
    return result

