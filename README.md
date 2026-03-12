# Database Interface System

A Python-based interface system that allows natural language interaction with both MySQL and MongoDB databases, featuring automatic error correction and seamless database switching.

## Prerequisites

- Python 3.8 or higher
- MySQL Server
- MongoDB Server
- Google Gemini API key (get it from [Google AI Studio](https://makersuite.google.com/app/apikey))

## Setup Instructions

1. **Get Gemini API Key**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Sign in with your Google account
   - Click on "Get API key" in the API section
   - Create a new API key or use an existing one
   - Copy the API key and keep it secure

2. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

3. **Create and Activate Virtual Environment**
   ```bash
   # Create virtual environment
   python -m venv chatdb_env

   # Activate virtual environment
   # For Windows:
   .\chatdb_env\Scripts\activate
   # For Unix/MacOS:
   source chatdb_env/bin/activate
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure Database Connections**

   In `run_full_interface_with_error_correction.py`, update the following:
   ```python
   # MySQL Connection (Line 384)
   mysql_conn = mysql.connector.connect(
       host="localhost",
       user="YOUR_MYSQL_USERNAME",
       password="YOUR_MYSQL_PASSWORD"
   )

   # MongoDB Connection (should stay the same) (Line 392)
   mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")

   # Gemini API Key
   client = genai.Client(api_key="YOUR_GEMINI_API_KEY")  # Required for natural language processing (Line 8)
   ```

   Note: The system uses the Gemini 2.0 Flash model for natural language processing.

## Loading Sample Databases

### Database Connection Details

The loading scripts use the following connection parameters:

```python
# MySQL Connection Parameters (in load_sqldb.py) (Line 7)
db_user = "YOUR_MYSQL_USERNAME"
db_password = "YOUR_MYSQL_PASSWORD"
db_host = "localhost"
db_name = "famous_painters_db"  # or "bike_store" for Bike Store database

# MongoDB Connection (in import_csv_to_mongodb.py) (Line 7)
client = MongoClient("mongodb://localhost:27017/")
db_name = "famous_painters_db" # or "bike_store" for Bike Store database

# Dataset Path (in load_sqldb.py) (Line 43)
csv_directory = "FamousPaintingDB"  # Path to dataset files

# Dataset Path (in import_csv_to_mongodb.py) (Line 12)
path = "FamousPaintingDB" # Path to dataset files

```

### Loading Bike Store Database

#### MySQL Setup
1. **Update Connection Details**
   In `load_sqldb.py`, ensure the MySQL configuration matches your setup:
   ```python
   db_user = "YOUR_MYSQL_USERNAME"
   db_password = "YOUR_MYSQL_PASSWORD"
   db_host = "localhost"
   db_name = "bike_store"
   csv_directory = "Bike_Store"  # Path to Bike Store CSV files
   ```

2. **Load Data**
   ```bash
   python load_sqldb.py
   ```
   Note: The script will automatically create the database if it doesn't exist.

#### MongoDB Setup (Alternative)
If you want to load Bike Store into MongoDB instead:
1. **Update Connection Details**
   In `import_csv_to_mongodb.py`, modify the configuration:
   ```python
   client = MongoClient("mongodb://localhost:27017/")
   db_name = "bike_store"
   path = "Bike_Store"  # Path to Bike Store CSV files
   ```

2. **Load Data**
   ```bash
   python import_csv_to_mongodb.py
   ```
   Note: MongoDB will automatically create the database when first used.

### Loading Famous Painting Database

#### MongoDB Setup
1. **Ensure MongoDB is Running**
   ```bash
   # MongoDB should be running on localhost:27017
   ```

2. **Update Connection Details**
   In `import_csv_to_mongodb.py`, verify the MongoDB configuration:
   ```python
   client = MongoClient("mongodb://localhost:27017/")
   db_name = "famous_painters_db"
   path = "FamousPaintingDB"  # Path to Famous Painting CSV files
   ```

3. **Load Data**
   ```bash
   python import_csv_to_mongodb.py
   ```
   Note: MongoDB will automatically create the database when first used.

#### MySQL Setup (Alternative)
If you want to load Famous Paintings into MySQL instead:
1. **Update Connection Details**
   In `load_sqldb.py`, modify the configuration:
   ```python
   db_user = "YOUR_MYSQL_USERNAME"
   db_password = "YOUR_MYSQL_PASSWORD"
   db_host = "localhost"
   db_name = "famous_painters_db"
   csv_directory = "FamousPaintingDB"  # Path to Famous Painting CSV files
   ```

2. **Load Data**
   ```bash
   python load_sqldb.py
   ```
   Note: The script will automatically create the database if it doesn't exist.

### Important Notes for Cross-Database Loading

1. **Schema Considerations**
   - When loading Bike Store into MongoDB, the relational schema will be converted to a document-based structure
   - When loading Famous Paintings into MySQL, the document structure will be normalized into relational tables

2. **Data Integrity**
   - Foreign key relationships in Bike Store will be maintained in MongoDB using references
   - Nested documents in Famous Paintings will be flattened into separate tables in MySQL

3. **Performance**
   - Consider the size of your datasets when choosing the database type
   - MongoDB might be more suitable for the Famous Paintings dataset due to its document structure
   - MySQL might be more efficient for the Bike Store dataset due to its relational nature

## Using the Interface

1. **Start the Interface**
   ```bash
   python run_full_interface_with_error_correction.py
   ```

2. **Available Commands**
   - List databases: "list databases"
   - Switch DBMS: "switch to SQL" or "switch to MongoDB"
   - Select database: "select database_name"
   - View schema: "show schema"
   - Execute query: Ask in natural language
   - Exit: "exit"

## Project Structure

```
.
├── run_full_interface_with_error_correction.py
├── load_sqldb.py
├── import_csv_to_mongodb.py
├── Bike_Store/
│   ├── brands.csv
│   ├── categories.csv
│   ├── customers.csv
│   ├── order_items.csv
│   ├── orders.csv
│   ├── products.csv
│   ├── staffs.csv
│   ├── stocks.csv
│   └── stores.csv
└── FamousPaintingDB/
    ├── artist.csv
    ├── canvas_size.csv
    ├── image_link.csv
    ├── museum.csv
    ├── museum_hours.csv
    ├── product_size.csv
    ├── subject.csv
    └── work.csv
```

## Notes

- Ensure MySQL and MongoDB servers are running before starting the interface
- The interface supports both SQL and MongoDB queries through natural language
- Error correction is automatic with up to 3 retry attempts
- Sample databases (Bike Store and Famous Painting) are included

## Troubleshooting

1. **Database Connection Issues**
   - Verify MySQL and MongoDB are running
   - Check credentials in the connection strings
   - Ensure proper permissions for database users

2. **API Key Issues**
   - Verify Gemini API key is valid
   - Check internet connectivity
   - Ensure API key has proper permissions
   - The system requires Gemini 2.0 Flash API access

3. **Data Loading Issues**
   - Verify CSV files are in correct locations
   - Check database permissions
   - Ensure proper database names are used
   - Make sure paths in scripts match your local directory structure 