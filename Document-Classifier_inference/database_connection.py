import json
import os
import sys

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.sql import text

from main import batch_predicts



def inference_updates(url_list):
    url_list = json.loads(url_list)  # Parse the JSON string into a list
    url_list = list(set(url_list))
    if len(url_list) == 0:
        return
    # Database connection parameters
    dbname = os.environ.get("POSTGRES_DB")
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    host = os.environ.get("POSTGRES_HOST")
    port = os.environ.get("POSTGRES_PORT")

    # Create the database URL
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    # Create an SQLAlchemy engine
    engine = create_engine(db_url)
    connection = engine.connect()
    transaction = connection.begin()
    # Execute the SQL query
    query = text(
        """
            SELECT *
            FROM sde_collections_candidateurl
            WHERE (
                document_type NOT IN :doc_types
                OR document_type IS NULL
            )
            AND inference_by <> :inferencer
            AND url IN :urls;
            """
    )
    df = pd.read_sql(
        query,
        connection,
        params={
            "doc_types": (1, 2, 3, 4, 5, 6),
            "urls": tuple(url_list),
            "inferencer": ("user"),
        },
    )
    url_list = df.url.values
    prediction = batch_predicts(
        "Document-Classifier_inference/config.json", url_list
    )
    transaction.commit()
    connection.close()
    connection = engine.connect()
    print("url_list:", list(prediction.keys()))
    print("document_type_list", list(prediction.values()))


if __name__ == "__main__":
    url_lists = sys.argv[1]

    inference_updates(url_lists)
