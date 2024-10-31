-- Databricks notebook source
CREATE OR REFRESH STREAMING TABLE bronze_stream_updates
(
  stream_id STRING,
  user_id STRING,
  user_login STRING,
  user_name STRING,
  game_id STRING,
  game_name STRING,
  viewer_count LONG,
  started_at STRING,
  language STRING,
  timestamp TIMESTAMP,
  is_mature BOOLEAN
)
as
SELECT 
  stream_id,
  user_id,
  user_login,
  user_name,
  game_id,
  game_name,
  viewer_count,
  started_at,
  language,
  timestamp,
  is_mature
 FROM cloud_files("${s3_path}", "parquet")
 WHERE CAST(timestamp AS DATE) >= date_sub(current_date(), 7);

-- COMMAND ----------

CREATE OR REFRESH STREAMING LIVE TABLE silver_twitch_streams ( 
  CONSTRAINT valid_timestamp EXPECT (timestamp IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_user_id EXPECT (timestamp IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_started_at_timestamp EXPECT (CAST(started_at AS TIMESTAMP) IS NOT NULL) ON VIOLATION DROP ROW
)
AS SELECT
    stream_id,
    timestamp,
    viewer_count,
    user_name,
    user_id,
    game_name,
    game_id,
    language,
    CAST(started_at AS TIMESTAMP) AS started_at
    
FROM STREAM(live.bronze_stream_updates);

-- COMMAND ----------

CREATE OR REFRESH STREAMING LIVE TABLE gold_game_metrics
AS SELECT
  timestamp,
  game_id,
  game_name,
  COUNT(user_id) as total_streamers,
  SUM(viewer_count) as total_viewer_count
FROM STREAM(live.silver_twitch_streams)
GROUP BY timestamp, game_id, game_name;

-- COMMAND ----------

CREATE OR REFRESH MATERIALIZED VIEW top_games_hour AS
WITH metrics AS (
  SELECT
    game_id,
    game_name,
    ROUND(SUM(total_viewer_count) * .25) as hours_watched,
    MAX(total_viewer_count) AS max_viewer_count,
    MAX(total_streamers) AS max_streamers_count
  FROM live.gold_game_metrics
  WHERE timestamp >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
  GROUP BY game_id, game_name
)
SELECT
  game_id,
  game_name,
  hours_watched,
  max_viewer_count,
  max_streamers_count,
  DENSE_RANK() OVER (ORDER BY hours_watched DESC) AS rank_by_hours_watched,
  DENSE_RANK() OVER (ORDER BY max_viewer_count DESC) AS rank_by_max_viewer
FROM
  metrics;

CREATE OR REFRESH MATERIALIZED VIEW top_games_day AS
WITH metrics AS (
  SELECT
    game_id,
    game_name,
    ROUND(SUM(total_viewer_count) * .25) as hours_watched,
    MAX(total_viewer_count) AS max_viewer_count,
    MAX(total_streamers) AS max_streamers_count
  FROM live.gold_game_metrics
  WHERE timestamp >= CURRENT_TIMESTAMP() - INTERVAL 1 DAY
  GROUP BY game_id, game_name
)
SELECT
  game_id,
  game_name,
  hours_watched,
  max_viewer_count,
  max_streamers_count,
  DENSE_RANK() OVER (ORDER BY hours_watched DESC) AS rank_by_hours_watched,
  DENSE_RANK() OVER (ORDER BY max_viewer_count DESC) AS rank_by_max_viewer
FROM
  metrics;

CREATE OR REFRESH MATERIALIZED VIEW top_games_week AS
WITH metrics AS (
  SELECT
    game_id,
    game_name,
    ROUND(SUM(total_viewer_count) * .25) as hours_watched,
    MAX(total_viewer_count) AS max_viewer_count,
    MAX(total_streamers) AS max_streamers_count
  FROM live.gold_game_metrics
  WHERE timestamp >= CURRENT_TIMESTAMP() - INTERVAL 1 WEEK
  GROUP BY game_id, game_name
)
SELECT
  game_id,
  game_name,
  hours_watched,
  max_viewer_count,
  max_streamers_count,
  DENSE_RANK() OVER (ORDER BY hours_watched DESC) AS rank_by_hours_watched,
  DENSE_RANK() OVER (ORDER BY max_viewer_count DESC) AS rank_by_max_viewer
FROM
  metrics;

-- COMMAND ----------

CREATE OR REFRESH MATERIALIZED VIEW top_streamers_hour AS
WITH metrics AS (
  SELECT
    user_id,
    user_name,
    MAX(viewer_count) as max_viewers,
    ROUND(SUM(viewer_count) * .25) as hours_watched
  FROM live.silver_twitch_streams
  WHERE timestamp >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
  GROUP BY user_id, user_name
)
SELECT
  user_id,
  user_name,
  max_viewers,
  hours_watched,
  DENSE_RANK() OVER (ORDER BY hours_watched DESC) AS rank_by_hours_watched,
  DENSE_RANK() OVER (ORDER BY max_viewers DESC) AS rank_by_max_viewers
FROM
  metrics;

CREATE OR REFRESH MATERIALIZED VIEW top_streamers_day AS
WITH metrics AS (
  SELECT
    user_id,
    user_name,
    MAX(viewer_count) as max_viewers,
    ROUND(SUM(viewer_count) * .25) as hours_watched
  FROM live.silver_twitch_streams
  WHERE timestamp >= CURRENT_TIMESTAMP() - INTERVAL 1 DAY
  GROUP BY user_id, user_name
)
SELECT
  user_id,
  user_name,
  max_viewers,
  hours_watched,
  DENSE_RANK() OVER (ORDER BY hours_watched DESC) AS rank_by_hours_watched,
  DENSE_RANK() OVER (ORDER BY max_viewers DESC) AS rank_by_max_viewers
FROM
  metrics;

CREATE OR REFRESH MATERIALIZED VIEW top_streamers_week AS
WITH metrics AS (
  SELECT
    user_id,
    user_name,
    MAX(viewer_count) as max_viewers,
    ROUND(SUM(viewer_count) * .25) as hours_watched
  FROM live.silver_twitch_streams
  WHERE timestamp >= CURRENT_TIMESTAMP() - INTERVAL 1 WEEK
  GROUP BY user_id, user_name
)
SELECT
  user_id,
  user_name,
  max_viewers,
  hours_watched,
  DENSE_RANK() OVER (ORDER BY hours_watched DESC) AS rank_by_hours_watched,
  DENSE_RANK() OVER (ORDER BY max_viewers DESC) AS rank_by_max_viewers
FROM
  metrics;

-- COMMAND ----------

CREATE OR REFRESH MATERIALIZED VIEW latest_stream_metrics AS
  SELECT
    SUM(viewer_count) as total_viewers,
    COUNT(stream_id) as total_streams,
    COUNT(DISTINCT game_id) as unique_games
  FROM live.silver_twitch_streams
  WHERE timestamp = (select MAX(timestamp) from live.silver_twitch_streams);

CREATE OR REFRESH MATERIALIZED VIEW latest_stream_metrics_hour AS
  SELECT
    SUM(viewer_count) as total_hours_,
    COUNT(stream_id) as total_streams,
    COUNT(DISTINCT game_id) as unique_games,
    ROUND(SUM(viewer_count) * .25) as hours_watched
  FROM live.silver_twitch_streams
  WHERE timestamp >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR;

CREATE OR REFRESH MATERIALIZED VIEW latest_stream_metrics_day AS
  SELECT
    SUM(viewer_count) as total_viewers,
    COUNT(stream_id) as total_streams,
    COUNT(DISTINCT game_id) as unique_games,
    ROUND(SUM(viewer_count) * .25) as hours_watched
  FROM live.silver_twitch_streams
  WHERE timestamp >= CURRENT_TIMESTAMP() - INTERVAL 1 DAY;

CREATE OR REFRESH MATERIALIZED VIEW latest_stream_metrics_week AS
  SELECT
    SUM(viewer_count) as total_viewers,
    COUNT(stream_id) as total_streams,
    COUNT(DISTINCT game_id) as unique_games,
    ROUND(SUM(viewer_count) * .25) as hours_watched
  FROM live.silver_twitch_streams
  WHERE timestamp >= CURRENT_TIMESTAMP() - INTERVAL 1 WEEK;

-- COMMAND ----------

CREATE OR REFRESH MATERIALIZED VIEW unique_streamers AS
SELECT
  DISTINCT user_name
FROM
  live.silver_twitch_streams;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC
