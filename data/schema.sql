CREATE DATABASE IF NOT EXISTS media_analytics;

USE media_analytics;

CREATE TABLE IF NOT EXISTS content_catalog
(
    content_id String,
    title String,
    content_type LowCardinality(String),
    genre LowCardinality(String),
    release_date Date,
    total_episodes UInt16
)
ENGINE = MergeTree()
ORDER BY (content_id);

CREATE TABLE IF NOT EXISTS episode_performance
(
    content_id String,
    episode_number UInt16,
    episode_date Date,
    viewers UInt64,
    unique_viewers UInt64,
    watch_time_minutes Float64,
    completion_rate Float64,
    returning_viewers UInt64,
    new_viewers UInt64,
    engagement_events UInt64
)
ENGINE = MergeTree()
ORDER BY (content_id, episode_number);

CREATE TABLE IF NOT EXISTS content_daily_metrics
(
    date Date,
    content_id String,
    views UInt64,
    unique_viewers UInt64,
    watch_time_minutes Float64,
    engagement_events UInt64,
    returning_viewers UInt64,
    new_viewers UInt64
)
ENGINE = MergeTree()
ORDER BY (content_id, date);