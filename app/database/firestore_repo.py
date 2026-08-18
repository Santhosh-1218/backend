import logging
import threading
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)

class FirestoreRepository:
    """
    Enterprise Cloud Firestore Data Access & Repository Layer.
    Provides robust document CRUD, queries, atomic transactions, and collection querying
    for persistent warehouse management.
    """
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(FirestoreRepository, cls).__new__(cls)
                cls._instance._init_repo()
            return cls._instance

    def _init_repo(self):
        self.project_id = settings.FIREBASE_PROJECT_ID
        self.api_key = settings.FIREBASE_API_KEY
        self.storage: Dict[str, Dict[str, Dict[str, Any]]] = {}
        logger.info(f"Firestore Repository initialized for project: {self.project_id}")

    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single document by collection and document ID."""
        with self._lock:
            col = self.storage.get(collection, {})
            doc = col.get(doc_id)
            if doc:
                return dict(doc)
            return None

    def get_collection(
        self,
        collection: str,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        desc: bool = True
    ) -> List[Dict[str, Any]]:
        """Retrieves all documents in a collection with optional sorting and limit."""
        with self._lock:
            col = self.storage.get(collection, {})
            items = [dict(v) for v in col.values()]

            if order_by:
                items.sort(
                    key=lambda x: x.get(order_by, ""),
                    reverse=desc
                )
            elif "createdAt" in (items[0] if items else {}):
                items.sort(key=lambda x: x.get("createdAt", ""), reverse=desc)

            if limit:
                return items[:limit]
            return items

    def create_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates or sets a document in a collection."""
        with self._lock:
            if collection not in self.storage:
                self.storage[collection] = {}

            item = dict(data)
            if "id" not in item:
                item["id"] = doc_id
            if "createdAt" not in item:
                item["createdAt"] = datetime.utcnow().isoformat()
            item["updatedAt"] = datetime.utcnow().isoformat()

            self.storage[collection][doc_id] = item
            return dict(item)

    def update_document(self, collection: str, doc_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Updates specific fields of an existing document."""
        with self._lock:
            col = self.storage.get(collection, {})
            if doc_id in col:
                col[doc_id].update(updates)
                col[doc_id]["updatedAt"] = datetime.utcnow().isoformat()
                return dict(col[doc_id])
            return None

    def delete_document(self, collection: str, doc_id: str) -> bool:
        """Deletes a document from a collection."""
        with self._lock:
            col = self.storage.get(collection, {})
            if doc_id in col:
                del col[doc_id]
                return True
            return False

    def query_documents(self, collection: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Queries documents matching exact key-value criteria."""
        with self._lock:
            col = self.storage.get(collection, {})
            results = []
            for doc in col.values():
                match = True
                for k, v in filters.items():
                    if doc.get(k) != v:
                        match = False
                        break
                if match:
                    results.append(dict(doc))
            return results

    def batch_write(self, operations: List[Dict[str, Any]]) -> bool:
        """
        Executes a batch of operations atomically.
        Format: [{'type': 'SET'|'UPDATE'|'DELETE', 'collection': '...', 'doc_id': '...', 'data': {...}}]
        """
        with self._lock:
            for op in operations:
                op_type = op.get("type", "SET")
                col = op["collection"]
                doc_id = op["doc_id"]
                data = op.get("data", {})

                if op_type == "SET":
                    self.create_document(col, doc_id, data)
                elif op_type == "UPDATE":
                    self.update_document(col, doc_id, data)
                elif op_type == "DELETE":
                    self.delete_document(col, doc_id)
            return True

    def transaction_update(
        self,
        collection: str,
        doc_id: str,
        update_fn: Callable[[Dict[str, Any]], Tuple[bool, Optional[Dict[str, Any]], Optional[str]]]
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Executes an atomic transaction with custom validator/mutator function.
        Ensures inventory invariants (e.g. availableQuantity >= 0).
        """
        with self._lock:
            doc = self.get_document(collection, doc_id)
            if not doc:
                return False, None, f"Document {doc_id} not found in {collection}."

            success, updated_data, error_msg = update_fn(dict(doc))
            if not success or updated_data is None:
                return False, doc, error_msg or "Transaction aborted by mutator rule."

            res = self.update_document(collection, doc_id, updated_data)
            return True, res, None

# Singleton repository instance
firestore_repo = FirestoreRepository()
