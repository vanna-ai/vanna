import unittest
from unittest.mock import MagicMock, patch

try:
    import pandas as pd
    from google.cloud import bigquery
    from vanna.legacy.google.bigquery_vector import BigQuery_VectorStore
    HAS_BIGQUERY = True
except ImportError:
    HAS_BIGQUERY = False

try:
    from vanna.legacy.pgvector.pgvector import PG_VectorStore
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

class TestSQLIFixes(unittest.TestCase):
    
    @unittest.skipIf(not HAS_BIGQUERY, "google-cloud-bigquery not installed")
    @patch('google.cloud.bigquery.Client')
    @patch('google.cloud.bigquery.Dataset')
    @patch('google.cloud.bigquery.Table')
    def test_bigquery_remove_training_data_parameterized(self, mock_table, mock_dataset, mock_client):
        # Setup mock
        client_instance = mock_client.return_value
        config = {"project_id": "test-project", "bigquery_dataset_name": "test_dataset"}
        
        # Initialize store
        with patch.object(BigQuery_VectorStore, 'generate_question_embedding', return_value=[0.1, 0.2]):
            store = BigQuery_VectorStore(config)
            
            # Test remove_training_data
            test_id = "1 OR 1=1"
            store.remove_training_data(id=test_id)
            
            # Verify query call
            args, kwargs = client_instance.query.call_args_list[-1]
            query = args[0]
            job_config = kwargs.get('job_config')
            
            self.assertIn("@id", query)
            self.assertNotIn(f"'{test_id}'", query)
            self.assertEqual(len(job_config.query_parameters), 1)
            self.assertEqual(job_config.query_parameters[0].name, "id")
            self.assertEqual(job_config.query_parameters[0].value, test_id)

    @unittest.skipIf(not HAS_BIGQUERY, "google-cloud-bigquery not installed")
    @patch('google.cloud.bigquery.Client')
    @patch('google.cloud.bigquery.Dataset')
    @patch('google.cloud.bigquery.Table')
    def test_bigquery_fetch_similar_parameterized(self, mock_table, mock_dataset, mock_client):
        # Setup mock
        client_instance = mock_client.return_value
        query_result_mock = MagicMock()
        query_result_mock.to_dataframe.return_value = pd.DataFrame()
        client_instance.query.return_value.result.return_value = query_result_mock
        
        config = {"project_id": "test-project", "bigquery_dataset_name": "test_dataset"}
        
        # Initialize store
        with patch.object(BigQuery_VectorStore, 'generate_question_embedding', return_value=[0.1, 0.2]):
            store = BigQuery_VectorStore(config)
            
            # Test fetch_similar_training_data
            test_type = "sql' OR '1'='1"
            store.fetch_similar_training_data(training_data_type=test_type, question="test?", n_results=10)
            
            # Verify query call
            found = False
            for call in client_instance.query.call_args_list:
                args, kwargs = call
                query = args[0]
                if "@training_data_type" in query:
                    job_config = kwargs.get('job_config')
                    self.assertNotIn(f"'{test_type}'", query)
                    self.assertEqual(job_config.query_parameters[0].name, "training_data_type")
                    self.assertEqual(job_config.query_parameters[0].value, test_type)
                    found = True
                    break
            self.assertTrue(found)

    @unittest.skipIf(not HAS_PGVECTOR, "langchain_postgres or sqlalchemy not installed")
    @patch('vanna.legacy.pgvector.pgvector.create_engine')
    @patch('vanna.legacy.pgvector.pgvector.PGVector')
    def test_pgvector_remove_collection_parameterized(self, mock_pgvector, mock_create_engine):
        # Setup mock
        engine_instance = mock_create_engine.return_value
        connection_mock = engine_instance.connect.return_value.__enter__.return_value
        
        config = {"connection_string": "postgresql://user:pass@host/db"}
        
        # Initialize store
        store = PG_VectorStore(config)
        
        # Test remove_collection
        store.remove_collection(collection_name="sql")
        
        # Verify execute call
        found = False
        for call in connection_mock.execute.call_args_list:
            args, kwargs = call
            params = args[1] if len(args) > 1 else kwargs
            if 'suffix' in params:
                self.assertEqual(params['suffix'], '%sql')
                found = True
                break
        self.assertTrue(found)

if __name__ == '__main__':
    unittest.main()
