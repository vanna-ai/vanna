## Evaluation of Vanna using TruLens Eval

1. [Install Trulens package](https://www.trulens.org/trulens_eval/install/).
2. In `evaluation/app_evaluation.py`, Configure the metrics to use, the test data (example user questions).
3. Run the script, and open dashboard at http://localhost:8501 to view results as they're processed.


### Compare multiple versions of the Vanna app
![alt text](images/trulens-2.png)

### See performance per-run of `vanna.generate_sql()`
![alt text](images/trulens-1.png)

### Overview of test results across multiple metrics
![alt text](images/trulens-3.png)
