# This is a Lambda function that is used as an interface to a SQL engine or database.
# It implements the main two functions that are needed by AI agents, `get_db_schema` and `execute_sql_query`.
# 
# The default implementation can create a local SQLite database for testing.

import sqlite3
import json
import os
import pandas as pd

db_name = 'baseball.db'

class SQLDatabase:
    def __init__(self, db_name: str):
        self.db_name = db_name

    def is_exist(self) -> bool:
        return os.path.isfile(self.db_name)

    def create_database_from_csv(self, csv_files):
        """Creates a SQLite database from multiple CSV files."""

        conn = sqlite3.connect(db_name)

        for csv_file in csv_files:
            # Read CSV into a DataFrame
            df = pd.read_csv(csv_file)

            # Get table name from CSV filename (without extension)
            table_name = csv_file.split('/')[-1].split('.')[0]

            # Create table and load data
            df.to_sql(table_name, conn, if_exists='replace', index=False)

        conn.close()
    

    def get_db_schema(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Get schema for player table
        cursor.execute("PRAGMA table_info(player)")
        player_schema = cursor.fetchall()
        
        # Get schema for salary table 
        cursor.execute("PRAGMA table_info(salary)")
        salary_schema = cursor.fetchall()
        
        conn.close()
        
        return json.dumps({
            'player': player_schema,
            'salary': salary_schema
        })    

    def execute_sql_query(self, sql_query: str):
    
        # Connect to SQLite database
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Execute query
        cursor.execute(sql_query)
        
        # Fetch results
        results = cursor.fetchall()
        
        # Get column names
        column_names = [description[0] for description in cursor.description]
        
        # Convert results to list of dicts
        results_list = []
        for row in results:
            row_dict = dict(zip(column_names, row))
            results_list.append(row_dict)
            
        # Close connection
        conn.close()
        
        # Return JSON string
        return json.dumps(results_list)

def lambda_handler(event, context):
    # Get the tool name from the input event
    tool_use = event

    db = SQLDatabase(db_name)
    # Check if the db exists in the /tmp directory
    if not db.is_exist():
        # Create the db using the csv files in the data directory
        db_files = ['sample-data/player.csv','sample-data/salary.csv']
        db.create_database_from_csv(db_files)

    # Once the db is ready, execute the requested method on the db
    if tool_use["name"] == 'get_db_schema':
        result = db.get_db_schema()
    elif tool_use["name"] == 'execute_sql_query':        
        # The SQL provided might cause ad error. We need to return the error message to the LLM
        # so it can fix the SQL and try again.
        try:
            result = db.execute_sql_query(tool_use['input']['sql_query'])
        except sqlite3.OperationalError as e:
            result = json.dumps({
                'error': str(e)
            })

    return {
        "type": "tool_result",
        "tool_use_id": tool_use["id"],
        "content": result
    }


if __name__ == "__main__":
    # Test event for get_db_schema
    test_event_get_db_schema = {
        "name": "get_db_schema",
        "id": "execute_sql_query_unique_id",
        "input": {},
        "type": "tool_use"
    }
    
    # Test event for execute_sql_query
    test_event_execute_sql_query = {
        "name": "execute_sql_query",
        "id": "execute_sql_query_unique_id",
        "input": {
            "sql_query": "SELECT count(*) FROM player"
        },
        "type": "tool_use"
    }
    
    # Call lambda handler with test events
    print("\nTesting get_db_schema:")
    response_get_db_schema = lambda_handler(test_event_get_db_schema, None)
    print(response_get_db_schema)
    
    print("\nTesting execute_sql_query:")
    response_execute_sql_query = lambda_handler(test_event_execute_sql_query, None)
    print(response_execute_sql_query)
