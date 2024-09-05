import os 
import json
import uuid
from typing import List, Dict, Any

import faiss
import numpy as np
import pandas as pd

from ..base import VannaBase
from ..exceptions import DependencyError

class FAISS(VannaBase):
    def __init__(self, config=None):
        if config is None:
            config = {}
        
        VannaBase.__init__(self, config=config)
        
        try:
            import faiss
        except ImportError:
            raise DependencyError(
                "FAISS is not installed. Please install it with 'pip install faiss-cpu' or 'pip install faiss-gpu'"
            )

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise DependencyError(
                "SentenceTransformer is not installed. Please install it with 'pip install sentence-transformers'."
            )
        
        self.path = config.get("path", ".")
        self.embedding_dim = config.get('embedding_dim', 384)
        self.n_results_sql = config.get('n_results_sql', config.get("n_results", 10))
        self.n_results_ddl = config.get('n_results_ddl', config.get("n_results", 10))
        self.n_results_documentation = config.get('n_results_documentation', config.get("n_results", 10))
        self.curr_client = config.get("client", "persistent")

        if self.curr_client == 'persistent':
            self.sql_index = self._load_or_create_index('sql_index.faiss')
            self.ddl_index = self._load_or_create_index('ddl_index.faiss')
            self.doc_index = self._load_or_create_index('doc_index.faiss')
        elif self.curr_client == 'in-memory':
            self.sql_index = faiss.IndexFlatL2(self.embedding_dim)
            self.ddl_index = faiss.IndexFlatL2(self.embedding_dim)
            self.doc_index = faiss.IndexFlatL2(self.embedding_dim)
        elif isinstance(self.curr_client, list) and len(self.curr_client) == 3 and all(isinstance(idx, faiss.Index) for idx in self.curr_client):
            self.sql_index = self.curr_client[0]
            self.ddl_index = self.curr_client[1]
            self.doc_index = self.curr_client[2]
        else:
            raise ValueError(f"Unsupported storage type was set in config: {self.curr_client}")

        self.sql_metadata: List[Dict[str, Any]] = self._load_or_create_metadata('sql_metadata.json')
        self.ddl_metadata: List[Dict[str, str]] = self._load_or_create_metadata('ddl_metadata.json')
        self.doc_metadata: List[Dict[str, str]] = self._load_or_create_metadata('doc_metadata.json')

        model_name = config.get('embedding_model', 'all-MiniLM-L6-v2')
        self.embedding_model = SentenceTransformer(model_name)

    def _load_or_create_index(self, filename):
        filepath = os.path.join(self.path, filename)
        if os.path.exists(filepath):
            return faiss.read_index(filepath)
        return faiss.IndexFlatL2(self.embedding_dim)

    def _load_or_create_metadata(self, filename):
        filepath = os.path.join(self.path, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return []

    def _save_index(self, index, filename):
        if self.curr_client == 'persistent':
            filepath = os.path.join(self.path, filename)
            faiss.write_index(index, filepath)

    def _save_metadata(self, metadata, filename):
        if self.curr_client == 'persistent':
            filepath = os.path.join(self.path, filename)
            with open(filepath, 'w') as f:
                json.dump(metadata, f)

    def generate_embedding(self, data: str, **kwargs) -> List[float]:
        embedding = self.embedding_model.encode(data)
        assert embedding.shape[0] == self.embedding_dim, \
            f"Embedding dimension mismatch: expected {self.embedding_dim}, got {embedding.shape[0]}"
        return embedding.tolist()

    def _add_to_index(self, index, metadata_list, text, extra_metadata=None) -> str:
        embedding = self.generate_embedding(text)
        index.add(np.array([embedding], dtype=np.float32))
        entry_id = str(uuid.uuid4())
        metadata_list.append({"id": entry_id, **(extra_metadata or {})})
        return entry_id
    
    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        entry_id = self._add_to_index(self.sql_index, self.sql_metadata, question + " " + sql, {"question": question, "sql": sql})
        self._save_index(self.sql_index, 'sql_index.faiss')
        self._save_metadata(self.sql_metadata, 'sql_metadata.json')
        return entry_id

    def add_ddl(self, ddl: str, **kwargs) -> str:
        entry_id = self._add_to_index(self.ddl_index, self.ddl_metadata, ddl, {"ddl": ddl})
        self._save_index(self.ddl_index, 'ddl_index.faiss')
        self._save_metadata(self.ddl_metadata, 'ddl_metadata.json')
        return entry_id

    def add_documentation(self, documentation: str, **kwargs) -> str:
        entry_id = self._add_to_index(self.doc_index, self.doc_metadata, documentation, {"documentation": documentation})
        self._save_index(self.doc_index, 'doc_index.faiss')
        self._save_metadata(self.doc_metadata, 'doc_metadata.json')
        return entry_id

    def _get_similar(self, index, metadata_list, text, n_results) -> list:
        embedding = self.generate_embedding(text)
        D, I = index.search(np.array([embedding], dtype=np.float32), k=n_results)
        return [] if len(I[0]) == 0 or I[0][0] == -1 else [metadata_list[i] for i in I[0]]

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        return self._get_similar(self.sql_index, self.sql_metadata, question, self.n_results_sql)
    
    def get_related_ddl(self, question: str, **kwargs) -> list:
        return [metadata["ddl"] for metadata in self._get_similar(self.ddl_index, self.ddl_metadata, question, self.n_results_ddl)]

    def get_related_documentation(self, question: str, **kwargs) -> list:
        return [metadata["documentation"] for metadata in self._get_similar(self.doc_index, self.doc_metadata, question, self.n_results_documentation)]

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        sql_data = pd.DataFrame(self.sql_metadata)
        sql_data['training_data_type'] = 'sql'

        ddl_data = pd.DataFrame(self.ddl_metadata)
        ddl_data['training_data_type'] = 'ddl'

        doc_data = pd.DataFrame(self.doc_metadata)
        doc_data['training_data_type'] = 'documentation'

        return pd.concat([sql_data, ddl_data, doc_data], ignore_index=True)

    def remove_training_data(self, id: str, **kwargs) -> bool:
        for metadata_list, index, index_name in [
            (self.sql_metadata, self.sql_index, 'sql_index.faiss'),
            (self.ddl_metadata, self.ddl_index, 'ddl_index.faiss'),
            (self.doc_metadata, self.doc_index, 'doc_index.faiss')
        ]:
            for i, item in enumerate(metadata_list):
                if item['id'] == id:
                    del metadata_list[i]
                    new_index = faiss.IndexFlatL2(self.embedding_dim)
                    embeddings = [self.generate_embedding(json.dumps(m)) for m in metadata_list]
                    if embeddings:
                        new_index.add(np.array(embeddings, dtype=np.float32))
                    setattr(self, index_name.split('.')[0], new_index)
                    
                    if self.curr_client == 'persistent':
                        self._save_index(new_index, index_name)
                        self._save_metadata(metadata_list, f"{index_name.split('.')[0]}_metadata.json")
                    
                    return True
        return False

    def remove_collection(self, collection_name: str) -> bool:
        if collection_name in ["sql", "ddl", "documentation"]:
            setattr(self, f"{collection_name}_index", faiss.IndexFlatL2(self.embedding_dim))
            setattr(self, f"{collection_name}_metadata", [])
            
            if self.curr_client == 'persistent':
                self._save_index(getattr(self, f"{collection_name}_index"), f"{collection_name}_index.faiss")
                self._save_metadata([], f"{collection_name}_metadata.json")
            
            return True
        return False