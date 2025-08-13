import sqlite3
import pandas as pd
import sys

# Set UTF-8 encoding to handle Thai characters
sys.stdout.reconfigure(encoding='utf-8')

# Connect to the database
conn = sqlite3.connect('elderdocs.db')

# Query all citizens with specific columns
df = pd.read_sql_query("SELECT id, status, error_reason, sanitized_filename FROM citizens", conn)

# Print the records
print("Citizen records:")
print(df.to_string())

# Close the connection
conn.close()