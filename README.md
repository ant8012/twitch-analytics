# Twitch Analytics Dashboard
A pipeline and dashboard for displaying metrics from the streaming site [Twitch.tv](https://www.twitch.tv/) This is a personal project not associated with Twitch.tv. 

![image](https://github.com/user-attachments/assets/b56fb3f9-a826-4957-8140-15db2e6a8b57)

![6Vi0azn88Q](https://github.com/user-attachments/assets/7e305f7e-2646-4f7e-9fae-82c8a55a24fb)

# Background
As an avid watcher of Twitch I wanted to get a better understanding of the trends in the streaming space. I wanted to answer questions such as:
- How does the total viewership of Twitch change over time?
- What are the top games/categories/streamers being streamed over different time periods (hour, day, week)?
- How much time are viewers spending on the platform?

To answer these questions I used [Twitch's API](https://dev.twitch.tv/docs/api/) to gather real time metrics on who is currently streaming and used
Databricks to perform processing and analytics.

# Architecture
![Untitled Diagram drawio (4)](https://github.com/user-attachments/assets/b0ac0294-0b14-46d8-9e3c-974dfeb1290d)

1. A Lambda function runs every 15 min and queries [this endpoint](https://dev.twitch.tv/docs/api/reference/#get-streams)
2. The endpoint returns all the current live streams and the result is written to a parquet file in S3.
3. A Delta Live Table (DLT) pipeline is configured in Databricks to run every couple hours to read the latest data via a streaming table.
4. The pipeline produces several materialized tables which are queried by a [Streamlit](https://streamlit.io/) app.

The lambda, S3 bucket, and the DLT pipeline are created by a Terraform configuration.

# Data Model
As mentioned, the data from [this endpoint](https://dev.twitch.tv/docs/api/reference/#get-streams) is written to parquet and read into Databricks.
The following tables are produced:

![db drawio (2)](https://github.com/user-attachments/assets/377c5589-c6d2-4daf-b506-ac9af0f97979)

- **bronze_stream_updates** - A streaming table that reads in the parquet files from S3 with any modifications.
- **silver_stream_updates** - A cleaned table that filters down the number of columns and drops any invalid rows (ex: those missing timestamps).
- **gold_game_metrics** - Contains aggregated metrics about each game/category.
- **top_streamers** - Materialized tables that rank streamers on total hours watched/max viewers within a given period (hour/day/week).
- **top_games** - Materialized tables that rank games on total hours watched/max viewers within a given period (hour/day/week).
- **latest_stream_metrics** - Materialized tables produce overall metrics such as total # of streams and viewers within a given period (hour/day/week).

# Implementation
The main components of this pipeline are detailed in the following PRs:

- Query Twitch stream data https://github.com/ant8012/twitch-analytics/pull/5
- Deploy Twitch update scripts to AWS https://github.com/ant8012/twitch-analytics/pull/8
- DLT pipeline for Twitch analytics https://github.com/ant8012/twitch-analytics/pull/10
- Creating streamlit dashboard for Twitch analytics https://github.com/ant8012/twitch-analytics/pull/15

# Rational
So why Databricks? Normally, given the relative size of the dataset a simple DBT pipeline with a self hosted database would be more sensible.
However, I wanted to take the opportunity to work with Databricks as a learning opportunity.

Lambda was a natural choice for running a short running script. For a personal project, it's free tier is generous, the only catch is that I would have to careful 
to avoid timing out the lambda function. Luckily, even with a single threaded application needing to call the API ~1000 times per 15 min (~100k streamers returned 100 entries at a time)
it takes ~4 min to run.

To process the resulting data I used DLT pipelines process the resulting data. DLT serverless was an appealing solution to build data pipelines easily without having to worry about sizing clusters though I could of used traditional notebooks with Databricks Jobs instead.

# Improvements
This project serves as a good starting point to analyze streaming trends but can be further expanded to answer more advanced questions.
For example, I wanted to integrate additional game metadata #13 to analyze the trends of the types of games being streamed.

Additionally, there are a number of improvements that can approve the monitorability, robustness, and data quaility. For example:
- Implement separate dev/prod environments [#14](https://github.com/ant8012/twitch-analytics/issues/14)
- Improve the query time of the deashboard [#12](https://github.com/ant8012/twitch-analytics/issues/12)
- Adding more data quality checks and handling schema evolution [#17](https://github.com/ant8012/twitch-analytics/issues/17)
