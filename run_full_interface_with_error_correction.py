from google import genai
import json
import pymongo
from bson.objectid import ObjectId
import mysql.connector

# Configure Gemini API
client = genai.Client(api_key="") ## enter your own api key

# Interpret user intent
def interpret_user_input(user_input):
    prompt = f"""
You are a database assistant.

Given this user input: \"{user_input}\"

Classify it into one of the following commands:
- list: if the user wants to list available databases or collections.
- switch: if the user wants to switch between SQL and MongoDB.
- select: if the user wants to use or switch to a specific database.
- query: if the user is asking a natural language query to be converted to SQL or MongoDB.
- schema_tables: if the user wants to view only the tables/collections in a database.
- schema_columns: if the user wants to view only the columns/attributes of a specific table/collection.
- schema_sample: if the user wants to view only a sample row from a specific table/collection.
- schema: if the user wants to view the complete schema of a database.
- exit: if the user wants to quit.

If you are unsure or the input does not fit any category, respond with:
{{"command": "unknown", "target": ""}}

Respond ONLY in this JSON format:
{{"command": "COMMAND", "target": "EXTRACTED_TARGET_OR_QUERY"}}
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        text = response.text.strip("```json\n").strip("```").strip()
        data = json.loads(text)

        command = data.get("command", "unknown").lower()
        target = data.get("target", "")

        if command not in ["list", "switch", "select", "query", "schema_tables", "schema_columns", "schema_sample", "schema", "exit"]:
            command = "unknown"

        return command, target

    except Exception as e:
        print("Could not parse Gemini response:", e)
        return "unknown", ""

# List databases or collections
def list_databases():
    if current_dbms == "mongodb":
        print("MongoDB Databases:")
        print(mongo_client.list_database_names())
    elif current_dbms == "sql":
        mysql_cursor.execute("SHOW DATABASES")
        print("MySQL Databases:")
        for db in mysql_cursor.fetchall():
            print(db[0])

# Get MongoDB schema
def get_mongodb_schema(db_name):
    try:
        db = mongo_client[db_name]
        collections = db.list_collection_names()
        
        schema_info = f"Database: {db_name}\nCollections:\n"
        
        for collection in collections:
            # Get a sample document to understand the structure
            sample_doc = db[collection].find_one()
            if sample_doc:
                # Convert ObjectId to string for JSON serialization
                for key, value in sample_doc.items():
                    if isinstance(value, ObjectId):
                        sample_doc[key] = str(value)
                
                schema_info += f"\nCollection: {collection}\n"
                schema_info += f"Sample document structure: {json.dumps(sample_doc, indent=2)}\n"
            else:
                schema_info += f"\nCollection: {collection} (empty)\n"
        
        return schema_info
    except Exception as e:
        return f"Error getting MongoDB schema: {str(e)}"

# Get MySQL schema
def get_mysql_schema(db_name):
    try:
        # Switch to the specified database
        mysql_cursor.execute(f"USE {db_name}")
        
        # Get all tables
        mysql_cursor.execute("SHOW TABLES")
        tables = mysql_cursor.fetchall()
        
        schema_info = f"Database: {db_name}\nTables:\n"
        
        for table in tables:
            table_name = table[0]
            schema_info += f"\nTable: {table_name}\n"
            
            # Get table structure
            mysql_cursor.execute(f"DESCRIBE {table_name}")
            columns = mysql_cursor.fetchall()
            
            schema_info += "Columns:\n"
            for column in columns:
                schema_info += f"  - {column[0]} ({column[1]})"
                if column[2] == "NO":
                    schema_info += " NOT NULL"
                if column[3] == "PRI":
                    schema_info += " PRIMARY KEY"
                if column[4] == "auto_increment":
                    schema_info += " AUTO_INCREMENT"
                schema_info += "\n"
            
            # Get a sample row
            mysql_cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
            sample_row = mysql_cursor.fetchone()
            if sample_row:
                schema_info += "Sample row:\n"
                schema_info += f"  {sample_row}\n"
        
        return schema_info
    except Exception as e:
        return f"Error getting MySQL schema: {str(e)}"

# Switch database
def switch_database(db_name):
    global current_mongo_db, current_sql_db
    if current_dbms == "mongodb":
        current_mongo_db = mongo_client[db_name]
        print(f"Switched to MongoDB database: {db_name}")
    elif current_dbms == "sql":
        try:
            mysql_conn.database = db_name
            current_sql_db = db_name
            print(f"Switched to SQL database: {db_name}")
        except mysql.connector.Error as err:
            print("Failed to switch SQL database:", err)

# Run natural language query
def convert_to_query(natural_query, db_type):
    # Get schema information based on the current database
    schema_info = ""
    if current_database:
        if current_dbms == "mongodb":
            schema_info = get_mongodb_schema(current_database)
        elif current_dbms == "sql":
            schema_info = get_mysql_schema(current_database)
    
    prompt = f"""
You are a database assistant. Convert this natural language query into {db_type} format.

Database Schema:
{schema_info}

Natural Language Query:
{natural_query}

Return ONLY the query and nothing else, inside triple backticks with a 'sql' or 'json' tag depending on the DBMS.
If the query is for MongoDB, use the proper MongoDB syntax in Python, not JSON. For example:
- For regular queries: db.collection.find({{"field": "value"}})
- For aggregation: db.collection.aggregate([
    {{"$match": {{"field": "value"}}}},
    {{"$group": {{"_id": "$field", "count": {{"$sum": 1}}}}}}
])
- For updates: 
  # Update one document
  db.collection.update_one(
    {{"field": "value"}},
    {{"$set": {{"field": "new_value"}}}}
  )
  # Update multiple documents
  db.collection.update_many(
    {{"field": "value"}},
    {{"$set": {{"field": "new_value"}}}}
  )
- For inserts: 
    db.collection.insert_one({{"field": "value"}})
    # For multiple inserts, use:
    db.collection.insert_many([
        {{"field": "value1"}},
        {{"field": "value2"}}
    ])

- For deletes: db.collection.delete_one({{"field": "value"}})

For SQL, use proper SQL syntax. For example: SELECT * FROM table WHERE field = 'value'
"""
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    query_text = response.text
    # Extract only inside ```sql ... ```
    if "```" in query_text:
        query_text = query_text.split("```")[1]
        query_text = query_text.strip().split("\n", 1)[1]  # Remove "sql" or "json" line
    return query_text.strip()

def fix_query(original_query, error_message, db_type):
    prompt = f"""
You are a database assistant. Fix this {db_type} query that resulted in an error.

Original Query:
{original_query}

Error Message:
{error_message}

Return ONLY the fixed query and nothing else, inside triple backticks with a 'sql' or 'json' tag depending on the DBMS.
If the query is for MongoDB, use the proper MongoDB syntax in Python, not JSON. For example: db.users.find() or db.users.aggregate()
"""
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    query_text = response.text
    # Extract only inside ```sql ... ```
    if "```" in query_text:
        query_text = query_text.split("```")[1]
        query_text = query_text.strip().split("\n", 1)[1]  # Remove "sql" or "json" line
    return query_text.strip()

def execute_query(query, db_type):
    max_attempts = 3
    attempt = 0
    last_error = None
    
    while attempt < max_attempts:
        try:
            if db_type == "sql":
                mysql_cursor.execute(query)
                results = mysql_cursor.fetchall()
                return results, None
            else:
                db = mongo_client[current_database]
                # Check if the query is a list of pipeline stages
                if isinstance(query, list):
                    # Execute the aggregation pipeline
                    exec_result = db.artist.aggregate(query)
                    results = list(exec_result)
                    return results, None
                else:
                    # Check if the query is a list of operations
                    if query.strip().startswith('[') and query.strip().endswith(']'):
                        # Execute each operation in the list
                        operations = eval(query)
                        results = []
                        for op in operations:
                            if hasattr(op, "inserted_ids"):
                                results.append(f"Documents inserted with IDs: {op.inserted_ids}")
                            elif hasattr(op, "inserted_id"):
                                results.append(f"Document inserted with ID: {op.inserted_id}")
                            elif hasattr(op, "modified_count"):
                                results.append(f"Modified {op.modified_count} document(s)")
                            elif hasattr(op, "deleted_count"):
                                results.append(f"Deleted {op.deleted_count} document(s)")
                        return {"message": "\n".join(results)}, None
                    else:
                        # Regular MongoDB query
                        exec_result = eval(f"{query}")
                        
                        # Handle different types of MongoDB operations
                        if hasattr(exec_result, "inserted_ids"):  # Insert many operation
                            return {"message": f"Documents inserted with IDs: {exec_result.inserted_ids}"}, None
                        elif hasattr(exec_result, "inserted_id"):  # Insert one operation
                            return {"message": f"Document inserted with ID: {exec_result.inserted_id}"}, None
                        elif hasattr(exec_result, "modified_count"):  # Update operation
                            return {"message": f"Modified {exec_result.modified_count} document(s)"}, None
                        elif hasattr(exec_result, "deleted_count"):  # Delete operation
                            return {"message": f"Deleted {exec_result.deleted_count} document(s)"}, None
                        elif hasattr(exec_result, "next"):  # Find operation
                            results = list(exec_result)
                            return results, None
                        else:
                            return exec_result, None
        except Exception as e:
            last_error = str(e)
            print(f"\nQuery error (attempt {attempt + 1}/{max_attempts}): {last_error}")
            
            if attempt < max_attempts - 1:
                print("Attempting to fix the query...")
                fixed_query = fix_query(query, last_error, db_type)
                print(f"Fixed query: {fixed_query}")
                query = fixed_query
            attempt += 1
    
    return None, last_error

# Get MongoDB tables/collections
def get_mongodb_tables(db_name):
    try:
        db = mongo_client[db_name]
        collections = db.list_collection_names()
        return f"Database: {db_name}\nCollections:\n" + "\n".join(f"- {collection}" for collection in collections)
    except Exception as e:
        return f"Error getting MongoDB collections: {str(e)}"

# Get MongoDB columns/attributes for a collection
def get_mongodb_columns(db_name, collection_name):
    try:
        db = mongo_client[db_name]
        collection = db[collection_name]
        sample_doc = collection.find_one()
        if sample_doc:
            # Convert ObjectId to string for JSON serialization
            for key, value in sample_doc.items():
                if isinstance(value, ObjectId):
                    sample_doc[key] = str(value)
            return f"Collection: {collection_name}\nAttributes:\n" + "\n".join(f"- {key}" for key in sample_doc.keys())
        else:
            return f"Collection {collection_name} is empty"
    except Exception as e:
        return f"Error getting MongoDB attributes: {str(e)}"

# Get MongoDB sample row
def get_mongodb_sample(db_name, collection_name):
    try:
        db = mongo_client[db_name]
        collection = db[collection_name]
        sample_doc = collection.find_one()
        if sample_doc:
            # Convert ObjectId to string for JSON serialization
            for key, value in sample_doc.items():
                if isinstance(value, ObjectId):
                    sample_doc[key] = str(value)
            return f"Collection: {collection_name}\nSample Document:\n{json.dumps(sample_doc, indent=2)}"
        else:
            return f"Collection {collection_name} is empty"
    except Exception as e:
        return f"Error getting MongoDB sample: {str(e)}"

# Get MySQL tables
def get_mysql_tables(db_name):
    try:
        mysql_cursor.execute(f"USE {db_name}")
        mysql_cursor.execute("SHOW TABLES")
        tables = mysql_cursor.fetchall()
        return f"Database: {db_name}\nTables:\n" + "\n".join(f"- {table[0]}" for table in tables)
    except Exception as e:
        return f"Error getting MySQL tables: {str(e)}"

# Get MySQL columns for a table
def get_mysql_columns(db_name, table_name):
    if db_name == None and current_database != None:
        db_name = current_database
    try:
        mysql_cursor.execute(f"USE {db_name}")
        mysql_cursor.execute(f"DESCRIBE {table_name}")
        columns = mysql_cursor.fetchall()
        return f"Table: {table_name}\nColumns:\n" + "\n".join(
            f"- {column[0]} ({column[1]})" + 
            (" NOT NULL" if column[2] == "NO" else "") +
            (" PRIMARY KEY" if column[3] == "PRI" else "") +
            (" AUTO_INCREMENT" if column[4] == "auto_increment" else "")
            for column in columns
        )
    except Exception as e:
        return f"Error getting MySQL columns: {str(e)}"

# Get MySQL sample row
def get_mysql_sample(db_name, table_name):
    try:
        mysql_cursor.execute(f"USE {db_name}")
        mysql_cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
        sample_row = mysql_cursor.fetchone()
        if sample_row:
            # Get column names
            mysql_cursor.execute(f"SHOW COLUMNS FROM {table_name}")
            columns = [column[0] for column in mysql_cursor.fetchall()]
            # Create a dictionary of column names and values
            sample_dict = dict(zip(columns, sample_row))
            return f"Table: {table_name}\nSample Row:\n{json.dumps(sample_dict, indent=2)}"
        else:
            return f"Table {table_name} is empty"
    except Exception as e:
        return f"Error getting MySQL sample: {str(e)}"

# --- SQL & Mongo Setup ---
mysql_conn = mysql.connector.connect(
    host="localhost", ## change to your own host
    user="tempuser", ## change to your own user
    password="TestPass123!" ## change to your own password
)
mysql_cursor = mysql_conn.cursor()

mongo_client = pymongo.MongoClient("mongodb://localhost:27017/") ## change to your own mongo client

# --- Initial state ---
current_dbms = "sql"
current_database = None

def main():
    global current_dbms, current_database

    print("Welcome to the DB Chatbot! Type 'exit' to quit.")

    while True:
        user_input = input(f"\nCurrent DBMS: {current_dbms} | Current Database: {current_database} | Your request: ")
        command, target = interpret_user_input(user_input)

        if command == "exit":
            print("Goodbye!")
            break

        elif command == "list":
            if current_dbms == "sql":
                mysql_cursor.execute("SHOW DATABASES")
                databases = mysql_cursor.fetchall()
                print("Available SQL databases:")
                for db in databases:
                    print("-", db[0])
            else:
                print("Available MongoDB databases:")
                for db in mongo_client.list_database_names():
                    print("-", db)

        elif command == "select":
            current_database = target
            if current_dbms == "sql":
                try:
                    mysql_cursor.execute(f"USE {current_database}")
                    print(f"Switched to SQL database: {current_database}")
                except Exception as e:
                    print("Error selecting SQL database:", e)
            else:
                if target in mongo_client.list_database_names():
                    print(f"Switched to MongoDB database: {target}")
                else:
                    print("MongoDB database not found.")

        elif command == "switch":
            if target.lower() == "sql":
                current_dbms = "sql"
                print("Switched to SQL.")
                current_database = None
            elif target.lower() == "mongodb":
                current_dbms = "mongodb"
                print("Switched to MongoDB.")
                current_database = None
            else:
                print("Unknown DBMS to switch to.")

        elif command == "schema":
            if not current_database and target:
                if current_dbms == "sql":
                    try:
                        mysql_cursor.execute(f"USE {target}")
                        current_database = target
                        print(f"Automatically switched to SQL database: {current_database}")
                    except Exception as e:
                        print("Error selecting SQL database:", e)
                        continue
                elif current_dbms == "mongodb":
                    if target in mongo_client.list_database_names():
                        current_database = target
                        print(f"Automatically switched to MongoDB database: {current_database}")
                    else:
                        print("MongoDB database not found.")
                        continue

            if not current_database:
                print("Please select a database first using the 'select' command.")
                continue
            
            print(f"\nSchema for {current_database} ({current_dbms.upper()}):")
            if current_dbms == "mongodb":
                schema_info = get_mongodb_schema(current_database)
            else:
                schema_info = get_mysql_schema(current_database)
            print(schema_info)

        elif command == "query":
            if not current_database:
                print("Please select a database first using the 'select' command.")
                continue

            generated_query = convert_to_query(target, "SQL" if current_dbms == "sql" else "MongoDB")
            print(f"\nGenerated {current_dbms.upper()} Query:\n{generated_query}")

            results, error = execute_query(generated_query, current_dbms)
            
            if error:
                print(f"\nFailed to execute query after 3 attempts. Last error: {error}")
            else:
                if results:
                    if isinstance(results, dict) and "message" in results:
                        print(results["message"])
                    else:
                        for row in results:
                            print(row)
                else:
                    print("Query executed successfully but returned no results.")

        elif command == "schema_tables":
            if not current_database and target:
                if current_dbms == "sql":
                    try:
                        mysql_cursor.execute(f"USE {target}")
                        current_database = target
                        print(f"Automatically switched to SQL database: {current_database}")
                    except Exception as e:
                        print("Error selecting SQL database:", e)
                        continue
                elif current_dbms == "mongodb":
                    if target in mongo_client.list_database_names():
                        current_database = target
                        print(f"Automatically switched to MongoDB database: {current_database}")
                    else:
                        print("MongoDB database not found.")
                        continue

            if not current_database:
                print("Please select a database first using the 'select' command.")
                continue
            
            print(f"\nTables/Collections in {current_database} ({current_dbms.upper()}):")
            if current_dbms == "mongodb":
                print(get_mongodb_tables(current_database))
            else:
                print(get_mysql_tables(current_database))

        elif command == "schema_columns":
            if not current_database:
                print("Please select a database first using the 'select' command.")
                continue
            
            if not target:
                print("Please specify a table/collection name.")
                continue
            
            print(f"\nColumns/Attributes for {target} in {current_database} ({current_dbms.upper()}):")
            if current_dbms == "mongodb":
                print(get_mongodb_columns(current_database, target))
            else:
                print(get_mysql_columns(current_database, target))

        elif command == "schema_sample":
            if not current_database:
                print("Please select a database first using the 'select' command.")
                continue
            
            if not target:
                print("Please specify a table/collection name.")
                continue
            
            print(f"\nSample row from {target} in {current_database} ({current_dbms.upper()}):")
            if current_dbms == "mongodb":
                print(get_mongodb_sample(current_database, target))
            else:
                print(get_mysql_sample(current_database, target))

        elif command == "unknown":
            print("Sorry, I couldn't understand what you meant. Try commands like 'list databases', 'switch to MongoDB', or ask a query.")

if __name__ == "__main__":
    main() 