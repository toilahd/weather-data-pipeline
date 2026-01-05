#!/usr/bin/env python3
"""
Quick script to check weather data in the database
"""
import sys
import os
from dotenv import load_dotenv
import psycopg2
from datetime import datetime

# Load environment
load_dotenv()

def connect_db():
    """Connect to PostgreSQL database"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', 5000),
        database=os.getenv('DB_NAME', 'db'),
        user=os.getenv('DB_USER', 'db_user'),
        password=os.getenv('DB_PASSWORD', 'db_password')
    )

def show_summary():
    """Show database summary statistics"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("=" * 80)
    print("WEATHER DATA SUMMARY")
    print("=" * 80)
    
    # Total records
    cursor.execute("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT city) as unique_cities,
            MIN(inserted_at) as first_record,
            MAX(inserted_at) as latest_record
        FROM dev.raw_weather_data
    """)
    total, cities, first, latest = cursor.fetchone()
    print(f"\nTotal Records: {total}")
    print(f"Unique Cities: {cities}")
    print(f"First Record:  {first}")
    print(f"Latest Record: {latest}")
    
    cursor.close()
    conn.close()

def show_latest(limit=10):
    """Show latest weather records"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print(f"LATEST {limit} WEATHER RECORDS")
    print("=" * 80)
    
    cursor.execute(f"""
        SELECT 
            city,
            temperature,
            feels_like,
            humidity,
            pressure,
            windspeed,
            precipitation,
            time,
            inserted_at
        FROM dev.raw_weather_data
        ORDER BY inserted_at DESC
        LIMIT {limit}
    """)
    
    print(f"\n{'City':<15} {'Temp':<6} {'Feels':<6} {'Humid':<6} {'Press':<8} {'Wind':<6} {'Rain':<6} {'Time':<20}")
    print("-" * 80)
    
    for row in cursor.fetchall():
        city, temp, feels, humid, press, wind, rain, time, inserted = row
        print(f"{city:<15} {temp:>5.1f}° {feels:>5.1f}° {humid:>5}% {press:>7.1f} {wind:>5.1f} {rain:>5.1f} {time}")
    
    cursor.close()
    conn.close()

def show_by_city():
    """Show latest record for each city"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print("CURRENT WEATHER BY CITY")
    print("=" * 80)
    
    cursor.execute("""
        WITH ranked AS (
            SELECT *,
                ROW_NUMBER() OVER (PARTITION BY city ORDER BY inserted_at DESC) as rn
            FROM dev.raw_weather_data
        )
        SELECT 
            city,
            temperature,
            feels_like,
            humidity,
            pressure,
            windspeed,
            cloud_cover,
            time
        FROM ranked
        WHERE rn = 1
        ORDER BY city
    """)
    
    print(f"\n{'City':<15} {'Temp':<6} {'Feels':<6} {'Humid':<6} {'Press':<8} {'Wind':<6} {'Cloud':<6} {'Time':<20}")
    print("-" * 90)
    
    for row in cursor.fetchall():
        city, temp, feels, humid, press, wind, cloud, time = row
        cloud = cloud if cloud is not None else 0
        print(f"{city:<15} {temp:>5.1f}° {feels:>5.1f}° {humid:>5}% {press:>7.1f} {wind:>5.1f} {cloud:>5}% {time}")
    
    cursor.close()
    conn.close()

def show_hourly_trend(city='Ha Noi', hours=24):
    """Show hourly temperature trend for a city"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print(f"HOURLY TEMPERATURE TREND - {city} (Last {hours} hours)")
    print("=" * 80)
    
    cursor.execute(f"""
        SELECT 
            time,
            temperature,
            humidity,
            windspeed,
            inserted_at
        FROM dev.raw_weather_data
        WHERE city = %s
        ORDER BY time DESC
        LIMIT {hours}
    """, (city,))
    
    print(f"\n{'Time':<20} {'Temp':<8} {'Humidity':<10} {'Wind Speed':<12} {'Inserted At':<20}")
    print("-" * 80)
    
    for row in cursor.fetchall():
        time, temp, humid, wind, inserted = row
        print(f"{time:<20} {temp:>6.1f}°C {humid:>8}% {wind:>10.1f} km/h {inserted}")
    
    cursor.close()
    conn.close()

def show_city_stats():
    """Show statistics grouped by city"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print("STATISTICS BY CITY")
    print("=" * 80)
    
    cursor.execute("""
        SELECT 
            city,
            COUNT(*) as records,
            ROUND(AVG(temperature)::numeric, 1) as avg_temp,
            ROUND(MIN(temperature)::numeric, 1) as min_temp,
            ROUND(MAX(temperature)::numeric, 1) as max_temp,
            ROUND(AVG(humidity)::numeric, 1) as avg_humidity
        FROM dev.raw_weather_data
        GROUP BY city
        ORDER BY city
    """)
    
    print(f"\n{'City':<15} {'Records':<10} {'Avg Temp':<10} {'Min Temp':<10} {'Max Temp':<10} {'Avg Humid':<10}")
    print("-" * 80)
    
    for row in cursor.fetchall():
        city, records, avg_temp, min_temp, max_temp, avg_humid = row
        print(f"{city:<15} {records:<10} {avg_temp:>8.1f}°C {min_temp:>8.1f}°C {max_temp:>8.1f}°C {avg_humid:>8.1f}%")
    
    cursor.close()
    conn.close()

def interactive_query():
    """Run custom SQL query"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print("INTERACTIVE SQL QUERY")
    print("=" * 80)
    print("\nEnter your SQL query (or 'exit' to quit):")
    print("Example: SELECT city, temperature FROM dev.raw_weather_data LIMIT 5;\n")
    
    while True:
        try:
            query = input("SQL> ").strip()
            if query.lower() in ['exit', 'quit', 'q']:
                break
            
            if not query:
                continue
                
            cursor.execute(query)
            
            if cursor.description:
                # Fetch results for SELECT queries
                columns = [desc[0] for desc in cursor.description]
                print("\n" + " | ".join(columns))
                print("-" * 80)
                
                for row in cursor.fetchall():
                    print(" | ".join(str(val) for val in row))
                print()
            else:
                # For INSERT/UPDATE/DELETE
                conn.commit()
                print(f"✓ Query executed successfully ({cursor.rowcount} rows affected)\n")
                
        except Exception as e:
            print(f"✗ Error: {e}\n")
    
    cursor.close()
    conn.close()

def main():
    """Main menu"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'summary':
            show_summary()
        elif command == 'latest':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            show_latest(limit)
        elif command == 'cities':
            show_by_city()
        elif command == 'trend':
            city = sys.argv[2] if len(sys.argv) > 2 else 'Ha Noi'
            hours = int(sys.argv[3]) if len(sys.argv) > 3 else 24
            show_hourly_trend(city, hours)
        elif command == 'stats':
            show_city_stats()
        elif command == 'sql':
            interactive_query()
        else:
            print(f"Unknown command: {command}")
            print_usage()
    else:
        # Default: show everything
        show_summary()
        show_by_city()
        show_city_stats()

def print_usage():
    """Print usage instructions"""
    print("""
Usage: python check_data.py [command] [options]

Commands:
  summary              Show database summary statistics
  latest [N]           Show latest N weather records (default: 10)
  cities               Show current weather for each city
  trend [city] [hrs]   Show hourly trend for a city (default: Ha Noi, 24 hours)
  stats                Show statistics grouped by city
  sql                  Interactive SQL query mode

Examples:
  python check_data.py                        # Show summary + cities + stats
  python check_data.py latest 20              # Show latest 20 records
  python check_data.py trend "Ho Chi Minh" 48 # Show 48-hour trend for HCMC
  python check_data.py sql                    # Enter SQL query mode
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
