# # from google.cloud.bigquery import dataset
# #
import src.vanna as vn
#
# import UNKNOWN
#
# vn.set_api_key(key="296375c50b68432e8c658395bf8a86ae")
# vn.set_dataset(dataset="demo-tpc-h") # this method is should be executed to set dataset to run vn.train
#
# # if question none
# vn.train()
#
# # if just sql
# vn.train(sql="SELECT AVG(salary) FROM employees")
#
# # if just ddl
# vn.train(ddl="CREATE TABLE employees (id INT, name VARCHAR())")
#
# # if just json_file
# vn.train(json_file="training_data/sample-imdb/questions.json")
#
# # if just sqlfile
# vn.train(sql="justsql.sql")

vn.connect_to_postgres(host='hh-pgsql-public.ebi.ac.uk', dbname='pfmegrnargs', user='reader', password='NWDMCE5xdipIjRrp', port=5432)
sql = "SELECT * FROM rnc_database"
query = vn.run_sql(sql=sql)
print(query)

# bq_sql = """-- This query shows a list of the daily top Google Search terms.
# SELECT
#    refresh_date AS Day,
#    term AS Top_Term,
#        -- These search terms are in the top 25 in the US each day.
#    rank,
# FROM `bigquery-public-data.google_trends.top_terms`
# WHERE
#    rank = 1
#        -- Choose only the top term each day.
#    AND refresh_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 WEEK)
#        -- Filter to the last 2 weeks.
# GROUP BY Day, Top_Term, rank
# ORDER BY Day DESC
#    -- Show the days in reverse chronological order.
# """
#
# # connect to bigquery function
# vn.connect_to_bigquery(project_id='pycob-prod', cred_file_path='creds.json')
#
# print(vn.run_sql(sql=bq_sql))

