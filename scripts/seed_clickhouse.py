
"""
Seed ClickHouse with synthetic media analytics dataset for demonstration.
"""

import os
import sys
from datetime import date, timedelta
from clickhouse_connect import get_client


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

def get_clickhouse_client(database=None):
    """Create and return a ClickHouse client."""
    host = os.getenv('CLICKHOUSE_HOST', 'localhost')
    port = int(os.getenv('CLICKHOUSE_PORT', 8123))
    username = os.getenv('CLICKHOUSE_USER', 'default')
    password = os.getenv('CLICKHOUSE_PASSWORD', '')
    secure = os.getenv('CLICKHOUSE_SECURE', 'false').lower() == 'true'

    client_kwargs = {
        'host': host,
        'port': port,
        'username': username,
        'password': password,
        'secure': secure
    }

    if database is not None:
        client_kwargs['database'] = database

    client = get_client(**client_kwargs)
    return client

def truncate_tables(client):
    """Truncate all tables to start fresh."""
    client.command('TRUNCATE TABLE media_analytics.content_catalog')
    client.command('TRUNCATE TABLE media_analytics.episode_performance')
    client.command('TRUNCATE TABLE media_analytics.content_daily_metrics')
    print("Truncated existing tables.")

def insert_content_catalog(client):
    """Insert content catalog entries for our scenarios."""

    catalog_data = [

        ('SHOW-001', 'The Great Adventure', 'series', 'Drama', date(2023, 1, 15), 8),

        ('SHOW-007', 'Mystery Manor', 'series', 'Mystery', date(2023, 3, 1), 8),

        ('SHOW-042', 'Lost in Space', 'series', 'Sci-Fi', date(2023, 2, 1), 8),

        ('SHOW-999', 'Short-lived Show', 'series', 'Comedy', date(2023, 5, 1), 2),
    ]

    client.insert(
        table='content_catalog',
        data=catalog_data,
        column_names=['content_id', 'title', 'content_type', 'genre', 'release_date', 'total_episodes']
    )
    print(f"Inserted {len(catalog_data)} content catalog entries.")

def generate_episode_performance(client):
    """Generate episode performance data for each scenario."""





    def generate_dates(start_date, count):
        return [start_date + timedelta(days=30*i) for i in range(count)]


    show001_data = []
    start_date = date(2023, 2, 1)
    episodes = 8
    dates = generate_dates(start_date, episodes)
    base_viewers = 10000
    base_completion = 0.8
    for i in range(episodes):
        episode_num = i + 1

        viewers = int(base_viewers * (1.0 + i * 0.05))

        completion = min(0.9, base_completion + i * 0.01)
        returning = int(viewers * 0.6 * completion)
        new_viewers = viewers - returning
        watch_time = viewers * 50 * completion
        engagement = int(viewers * 10 * completion)

        show001_data.append([
            'SHOW-001',
            episode_num,
            dates[i],
            viewers,
            int(viewers * 0.85),
            watch_time,
            completion,
            returning,
            new_viewers,
            engagement
        ])


    show007_data = []
    start_date = date(2023, 3, 15)
    episodes = 8
    dates = generate_dates(start_date, episodes)
    base_viewers = 15000
    base_completion = 0.7
    for i in range(episodes):
        episode_num = i + 1

        viewers = int(base_viewers * (1.0 - i * 0.08))

        completion = max(0.3, base_completion - i * 0.06)
        returning = int(viewers * 0.4 * completion)
        new_viewers = viewers - returning
        watch_time = viewers * 45 * completion
        engagement = int(viewers * 8 * completion)

        show007_data.append([
            'SHOW-007',
            episode_num,
            dates[i],
            viewers,
            int(viewers * 0.8),
            watch_time,
            completion,
            returning,
            new_viewers,
            engagement
        ])


    show042_data = []
    start_date = date(2023, 2, 1)
    episodes = 8
    dates = generate_dates(start_date, episodes)
    base_viewers = 12000
    base_completion = 0.75
    for i in range(episodes):
        episode_num = i + 1
        viewers = int(base_viewers * (1.0 - i * 0.04))

        if i == 2:
            completion = base_completion - 0.25
        else:
            completion = base_completion - i * 0.02
        completion = max(0.2, completion)
        returning = int(viewers * 0.5 * completion)
        new_viewers = viewers - returning
        watch_time = viewers * 48 * completion
        engagement = int(viewers * 9 * completion)

        show042_data.append([
            'SHOW-042',
            episode_num,
            dates[i],
            viewers,
            int(viewers * 0.82),
            watch_time,
            completion,
            returning,
            new_viewers,
            engagement
        ])


    show999_data = []
    start_date = date(2023, 5, 1)
    episodes = 2
    dates = generate_dates(start_date, episodes)
    base_viewers = 500
    base_completion = 0.6
    for i in range(episodes):
        episode_num = i + 1
        viewers = int(base_viewers * (1.0 - i * 0.1))
        completion = base_completion - i * 0.05
        completion = max(0.3, completion)
        returning = int(viewers * 0.5 * completion)
        new_viewers = viewers - returning
        watch_time = viewers * 40 * completion
        engagement = int(viewers * 5 * completion)

        show999_data.append([
            'SHOW-999',
            episode_num,
            dates[i],
            viewers,
            int(viewers * 0.75),
            watch_time,
            completion,
            returning,
            new_viewers,
            engagement
        ])


    all_data = show001_data + show007_data + show042_data + show999_data
    client.insert(
        table='episode_performance',
        data=all_data,
        column_names=[
            'content_id', 'episode_number', 'episode_date', 'viewers', 'unique_viewers',
            'watch_time_minutes', 'completion_rate', 'returning_viewers', 'new_viewers', 'engagement_events'
        ]
    )
    print(f"Inserted {len(all_data)} episode performance records.")

def generate_daily_metrics(client):
    """Generate optional daily metrics (not strictly needed for episode-based analysis)."""


    print("Skipping daily metrics generation for MVP.")


def main():
    """Main seeding function."""
    print("Connecting to ClickHouse...")


    host = os.getenv('CLICKHOUSE_HOST', 'localhost')
    port = int(os.getenv('CLICKHOUSE_PORT', 8123))
    username = os.getenv('CLICKHOUSE_USER', 'default')
    password = os.getenv('CLICKHOUSE_PASSWORD', '')
    secure = os.getenv('CLICKHOUSE_SECURE', 'false').lower() == 'true'

    try:
        client = get_client(
            host=host,
            port=port,
            username=username,
            password=password,
            secure=secure
        )
        client.ping()
        print("Connected to ClickHouse successfully.")
    except Exception as e:
        print(f"Failed to connect to ClickHouse: {e}")
        sys.exit(1)


    client.command('CREATE DATABASE IF NOT EXISTS media_analytics')
    print("Ensured database 'media_analytics' exists.")


    database = os.getenv('CLICKHOUSE_DATABASE', 'media_analytics')
    client = get_client(
        host=host,
        port=port,
        username=username,
        password=password,
        database=database,
        secure=secure
    )

    client.ping()
    print(f"Connected to database '{database}'.")


    schema_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'schema.sql')
    with open(schema_path, 'r') as f:
        schema_sql = f.read()


    statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
    for statement in statements:
        if statement:
            try:
                client.command(statement)
            except Exception as e:


                if 'already exists' not in str(e).lower() and 'unknown database' not in str(e).lower():
                    print(f"Warning: Failed to execute statement: {statement[:100]}... Error: {e}")

    print("Ensured database schema exists.")


    truncate_tables(client)
    insert_content_catalog(client)
    generate_episode_performance(client)
    generate_daily_metrics(client)

    print("Seeding complete!")

if __name__ == '__main__':
    main()