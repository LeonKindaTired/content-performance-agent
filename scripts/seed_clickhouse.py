#!/usr/bin/env python3
"""
Seed ClickHouse with synthetic media analytics dataset for demonstration.
"""

import os
import sys
from datetime import date, timedelta
from clickhouse_connect import get_client

# Add the project root to the path so we can import config if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

def get_clickhouse_client():
    """Create and return a ClickHouse client."""
    host = os.getenv('CLICKHOUSE_HOST', 'localhost')
    port = int(os.getenv('CLICKHOUSE_PORT', 8123))
    username = os.getenv('CLICKHOUSE_USER', 'default')
    password = os.getenv('CLICKHOUSE_PASSWORD', '')
    database = os.getenv('CLICKHOUSE_DATABASE', 'media_analytics')
    secure = os.getenv('CLICKHOUSE_SECURE', 'false').lower() == 'true'

    client = get_client(
        host=host,
        port=port,
        username=username,
        password=password,
        database=database,
        secure=secure
    )
    return client

def truncate_tables(client):
    """Truncate all tables to start fresh."""
    client.command('TRUNCATE TABLE media_analytics.content_catalog')
    client.command('TRUNCATE TABLE media_analytics.episode_performance')
    client.command('TRUNCATE TABLE media_analytics.content_daily_metrics')
    print("Truncated existing tables.")

def insert_content_catalog(client):
    """Insert content catalog entries for our scenarios."""
    # Format: (content_id, title, content_type, genre, release_date, total_episodes)
    catalog_data = [
        # SHOW-001: Successful show
        ('SHOW-001', 'The Great Adventure', 'series', 'Drama', '2023-01-15', 8),
        # SHOW-007: Acquisition strong, retention weak
        ('SHOW-007', 'Mystery Manor', 'series', 'Mystery', '2023-03-01', 8),
        # SHOW-042: Failing show (declining retention)
        ('SHOW-042', 'Lost in Space', 'series', 'Sci-Fi', '2023-02-01', 8),
        # SHOW-999: Insufficient evidence (very few episodes)
        ('SHOW-999', 'Short-lived Show', 'series', 'Comedy', '2023-05-01', 2),
    ]

    client.insert(
        table='content_catalog',
        data=catalog_data,
        column_names=['content_id', 'title', 'content_type', 'genre', 'release_date', 'total_episodes']
    )
    print(f"Inserted {len(catalog_data)} content catalog entries.")

def generate_episode_performance(client):
    """Generate episode performance data for each scenario."""

    # We'll generate data for 8 episodes for most shows, 2 for SHOW-999
    # Data is deterministic based on the scenario.

    # Helper to generate date series
    def generate_dates(start_date, count):
        return [start_date + timedelta(days=30*i) for i in range(count)]  # Monthly releases

    # SHOW-001: Successful show - high completion, stable/increasing retention, healthy acquisition
    show001_data = []
    start_date = date(2023, 2, 1)
    episodes = 8
    dates = generate_dates(start_date, episodes)
    base_viewers = 10000
    base_completion = 0.8
    for i in range(episodes):
        episode_num = i + 1
        # Slight growth in viewers
        viewers = int(base_viewers * (1.0 + i * 0.05))
        # Completion rate slightly increasing or stable
        completion = min(0.9, base_completion + i * 0.01)
        returning = int(viewers * 0.6 * completion)  # 60% of viewers are returning, scaled by completion
        new_viewers = viewers - returning
        watch_time = viewers * 50 * completion  # 50 minutes per viewer if they completed fully
        engagement = int(viewers * 10 * completion)  # 10 engagement events per viewer on average

        show001_data.append([
            'SHOW-001',
            episode_num,
            dates[i],
            viewers,
            int(viewers * 0.85),  # unique viewers ~85% of total
            watch_time,
            completion,
            returning,
            new_viewers,
            engagement
        ])

    # SHOW-007: Acquisition strong, retention weak - strong initial acquisition but poor retention
    show007_data = []
    start_date = date(2023, 3, 15)
    episodes = 8
    dates = generate_dates(start_date, episodes)
    base_viewers = 15000  # High initial acquisition
    base_completion = 0.7  # Starts decent
    for i in range(episodes):
        episode_num = i + 1
        # Viewers decline slowly due to poor retention
        viewers = int(base_viewers * (1.0 - i * 0.08))  # 8% decline per episode
        # Completion drops significantly
        completion = max(0.3, base_completion - i * 0.06)  # Drops by 6% each episode
        returning = int(viewers * 0.4 * completion)  # Lower returning ratio
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

    # SHOW-042: Failing show - declining completion, concentrated episode drop-off
    show042_data = []
    start_date = date(2023, 2, 1)
    episodes = 8
    dates = generate_dates(start_date, episodes)
    base_viewers = 12000
    base_completion = 0.75
    for i in range(episodes):
        episode_num = i + 1
        viewers = int(base_viewers * (1.0 - i * 0.04))  # Slow decline in total viewers
        # Significant drop at episode 3 (index 2)
        if i == 2:  # Episode 3
            completion = base_completion - 0.25  # Big drop
        else:
            completion = base_completion - i * 0.02  # Gradual decline
        completion = max(0.2, completion)  # Don't go below 20%
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

    # SHOW-999: Insufficient evidence - only 2 episodes with low viewers
    show999_data = []
    start_date = date(2023, 5, 1)
    episodes = 2
    dates = generate_dates(start_date, episodes)
    base_viewers = 500  # Very low viewership
    base_completion = 0.6
    for i in range(episodes):
        episode_num = i + 1
        viewers = int(base_viewers * (1.0 - i * 0.1))  # Small decline
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

    # Insert all data
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
    # For simplicity, we'll skip daily metrics for now as the spec focuses on episode performance.
    # But we can insert some dummy data to satisfy the schema.
    print("Skipping daily metrics generation for MVP.")
    # In a real implementation, we would generate daily aggregates from episode data.

def main():
    """Main seeding function."""
    print("Connecting to ClickHouse...")
    client = get_clickhouse_client()

    # Test connection
    try:
        client.ping()
        print("Connected to ClickHouse successfully.")
    except Exception as e:
        print(f"Failed to connect to ClickHouse: {e}")
        sys.exit(1)

    # Ensure database exists
    client.command('CREATE DATABASE IF NOT EXISTS media_analytics')

    # Truncate and reseed
    truncate_tables(client)
    insert_content_catalog(client)
    generate_episode_performance(client)
    generate_daily_metrics(client)

    print("Seeding complete!")

if __name__ == '__main__':
    main()