from api_request import fetch_data, fetch_mock_data
import psycopg2
import os
from dotenv import load_dotenv 


load_dotenv()

def connect_to_db():
    try:  
        # Check if running in Docker (Airflow container)
        # In Docker, the PostgreSQL service is accessible via 'db:5432'
        # On host, it's accessible via 'localhost:5000'
        
        # Try Docker environment first (for Airflow)
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT)
        print(f"Attempting to connect to {db_host}:{db_port}")
        
        conn = psycopg2.connect(
            host=db_host,
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=db_port
        )
        print(f"Successfully connected to database at {db_host}:{db_port}")
        return conn
    except psycopg2.Error as e:
        print("Error connecting to the database:", e)
        raise
    
def create_table(conn):
    print("Create table if not exist....")
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE SCHEMA IF NOT EXISTS dev;
            CREATE TABLE IF NOT EXISTS dev.raw_weather_data (
                id SERIAL PRIMARY KEY,
                city VARCHAR(255),
                temperature FLOAT,
                weather_description TEXT,
                wind_speed FLOAT,
                time TIMESTAMP,
                inserted_at TIMESTAMP DEFAULT NOW(),
                utc_offset TEXT
            )
        """)
        conn.commit()
        print("Table created successfully")
    except psycopg2.Error as e:
        print("Error creating table:", e)
        conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()

def insert_records(conn, data):
    print("Inserting weather data into database")
    cursor = None
    try:
        weather = data['current']
        location = data['location']
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dev.raw_weather_data (
                city,
                temperature,
                weather_description,
                wind_speed,
                time, 
                inserted_at,
                utc_offset
            ) VALUES (%s, %s, %s, %s, %s, NOW(), %s)          
                """, (
                    location['name'],
                    weather['temperature'],
                    weather['weather_descriptions'][0],
                    weather['wind_speed'],
                    location['localtime'],
                    location['utc_offset']
                ))
        conn.commit()
        print("Data sucessfully inserted.")
    except psycopg2.Error as e:
        print("Error inserting data:", e)
        conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
def main():
    conn = None  # Initialize conn to avoid UnboundLocalError
    try:
        data = fetch_mock_data()
        conn = connect_to_db()
        create_table(conn)
        insert_records(conn, data)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()