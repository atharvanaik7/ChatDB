import os
import pandas as pd
from sqlalchemy import create_engine
import mysql.connector
from mysql.connector import errorcode

# Database connection details
db_user = "tempuser" ## Change this to your username
db_password = "TestPass123!" ## Change this to your password
db_host = "localhost"  # e.g., "localhost"
db_name = "famous_painters_db" ## Change this to the name of the database you want to create

# Create a MySQL connection (without selecting a specific database initially)
conn = mysql.connector.connect(
    user=db_user, password=db_password, host=db_host
)

cursor = conn.cursor()

# Check if the database exists, create it if not
try:
    cursor.execute(f"USE {db_name}")
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_BAD_DB_ERROR:
        print(f"Database '{db_name}' does not exist. Creating it...")
        cursor.execute(f"CREATE DATABASE {db_name}")
        print(f"Database '{db_name}' created successfully.")
        conn.commit()
    else:
        print(f"Error: {err}")
        cursor.close()
        conn.close()
        exit()

# Close the initial connection to create the engine with the new database
cursor.close()
conn.close()

# Create a SQLAlchemy engine with the newly created or existing database
engine = create_engine(f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}")

# Directory containing CSV files
csv_directory = "FamousPaintingDB"  # Change this to your CSV directory

# Loop through all CSV files in the directory
for file in os.listdir(csv_directory):
    if file.endswith(".csv"):
        file_path = os.path.join(csv_directory, file)
        
        # Load CSV into DataFrame
        df = pd.read_csv(file_path)
        
        # Convert filename to table name (remove extension, replace spaces)
        table_name = os.path.splitext(file)[0].replace(" ", "_")
        
        # Save DataFrame to MySQL
        df.to_sql(table_name, engine, if_exists="replace", index=False)

        print(f"Table '{table_name}' created successfully with {len(df)} records.")

print("All CSV files have been loaded into MySQL.")
