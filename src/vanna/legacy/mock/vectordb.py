import pandas as pd

from ..base import VannaBase


class MockVectorDB(VannaBase):
    def __init__(self, config=None):
        pass

    def _get_id(self, value: str, **kwargs) -> str:
        # Hash the value and return the ID
        return str(hash(value))

    def add_ddl(self, ddl: str, **kwargs) -> str:
        return self._get_id(ddl)

    def add_documentation(self, doc: str, **kwargs) -> str:
        return self._get_id(doc)

    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        return self._get_id(question)

    def get_related_ddl(self, question: str, **kwargs) -> list:
        return []

    def get_related_documentation(self, question: str, **kwargs) -> list:
        return []

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        return []

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        return pd.DataFrame({'id': {0: '19546-ddl',
  1: '91597-sql',
  2: '133976-sql',
  3: '59851-doc',
  4: '73046-sql'},
 'training_data_type': {0: 'ddl',
  1: 'sql',
  2: 'sql',
  3: 'documentation',
  4: 'sql'},
 'question': {0: None,
  1: 'What are the top selling genres?',
  2: 'What are the low 7 artists by sales?',
  3: None,
  4: 'What is the total sales for each customer?'},
 'content': {0: 'CREATE TABLE [Invoice]\n(\n    [InvoiceId] INTEGER  NOT NULL,\n    [CustomerId] INTEGER  NOT NULL,\n    [InvoiceDate] DATETIME  NOT NULL,\n    [BillingAddress] NVARCHAR(70),\n    [BillingCity] NVARCHAR(40),\n    [BillingState] NVARCHAR(40),\n    [BillingCountry] NVARCHAR(40),\n    [BillingPostalCode] NVARCHAR(10),\n    [Total] NUMERIC(10,2)  NOT NULL,\n    CONSTRAINT [PK_Invoice] PRIMARY KEY  ([InvoiceId]),\n    FOREIGN KEY ([CustomerId]) REFERENCES [Customer] ([CustomerId]) \n\t\tON DELETE NO ACTION ON UPDATE NO ACTION\n)',
  1: 'SELECT g.Name AS Genre, SUM(il.Quantity) AS TotalSales\nFROM Genre g\nJOIN Track t ON g.GenreId = t.GenreId\nJOIN InvoiceLine il ON t.TrackId = il.TrackId\nGROUP BY g.GenreId, g.Name\nORDER BY TotalSales DESC;',
  2: 'SELECT a.ArtistId, a.Name, SUM(il.Quantity) AS TotalSales\nFROM Artist a\nINNER JOIN Album al ON a.ArtistId = al.ArtistId\nINNER JOIN Track t ON al.AlbumId = t.AlbumId\nINNER JOIN InvoiceLine il ON t.TrackId = il.TrackId\nGROUP BY a.ArtistId, a.Name\nORDER BY TotalSales ASC\nLIMIT 7;',
  3: 'This is a SQLite database. For dates rememeber to use SQLite syntax.',
  4: 'SELECT c.CustomerId, c.FirstName, c.LastName, SUM(i.Total) AS TotalSales\nFROM Customer c\nJOIN Invoice i ON c.CustomerId = i.CustomerId\nGROUP BY c.CustomerId, c.FirstName, c.LastName;'}})

    def remove_training_data(id: str, **kwargs) -> bool:
        return True
