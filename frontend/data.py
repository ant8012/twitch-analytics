import os

from databricks import sql

import pandas as pd
import streamlit as st


@st.cache_resource(ttl=300)
def get_connection():
    return sql.connect(
        server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
        http_path=os.getenv("DATABRICKS_HTTP_PATH"),
        access_token=os.getenv("DATABRICKS_TOKEN"),
    )


def execute_query(table, query):
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.columns(schema_name="twitch_test", table_name=table)
        cursor.execute(query)
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]

        return pd.DataFrame(rows, columns=column_names)

@st.cache_data(ttl=7200)
def get_top_games(timescale):
    table_name = ""
    if timescale == "Hour":
        table_name = "top_games_hour"
    elif timescale == "Day":
        table_name = "top_games_day"
    elif timescale == "Week":
        table_name = "top_games_week"

    query = f"SELECT * FROM {table_name} ORDER BY hours_watched DESC LIMIT 100"
    df = execute_query(table_name, query)

    df.rename(
        columns={
            "game_name": "Name",
            "hours_watched": "Hours Watched",
            "max_viewer_count": "Highest # of Viewers",
            "max_streamers_count": "Highest # of Streamers",
        },
        inplace=True,
    )
    return df


@st.cache_data(ttl=7200)
def get_top_streamers(timescale):
    table_name = ""
    if timescale == "Hour":
        table_name = "top_streamers_hour"
    elif timescale == "Day":
        table_name = "top_streamers_day"
    elif timescale == "Week":
        table_name = "top_streamers_week"

    query = f"SELECT * FROM {table_name} ORDER BY hours_watched DESC LIMIT 1000"
    df = execute_query(table_name, query)
    df.rename(
        columns={
            "user_name": "Name",
            "hours_watched": "Hours Watched",
            "max_viewers": "Highest # of Viewers",
        },
        inplace=True,
    )
    return df


@st.cache_data(ttl=7200)
def get_stream_metrics(timescale):
    table_name = ""
    if timescale == "Hour":
        table_name = "latest_stream_metrics_hour"
    elif timescale == "Day":
        table_name = "latest_stream_metrics_day"
    elif timescale == "Week":
        table_name = "latest_stream_metrics_week"

    query = f"SELECT * FROM {table_name}"
    df = execute_query(table_name, query)
    return df


@st.cache_data(ttl=7200)
def get_viewers(streamer: None):
    print(streamer)
    query = """SELECT
        date_format(timestamp, 'MMM d HH:mm') as timestamp,
        SUM(viewer_count) as total_viewers 
    FROM
        silver_twitch_streams
    WHERE
        timestamp >= CURRENT_TIMESTAMP() - INTERVAL 7 DAY
    """

    if streamer:
        query += """
            AND user_name = \"{streamer}\"
    """.format(streamer=streamer)
        
    query +="""
    GROUP BY
        timestamp
    ORDER BY
        timestamp ASC"""
    df = execute_query("silver_twitch_streams", query)
    return df


@st.cache_data(ttl=7200)
def get_latest_stream_metrics():
    query = "SELECT * FROM latest_stream_metrics"
    df = execute_query("latest_stream_metrics", query)
    return df

@st.cache_data(ttl=7200)
def get_streamer_list(term: None):
    df = get_top_streamers("Week")
    streamer_list = df["Name"].to_list()
    if term:
        term = term.lower()
        streamer_list = [streamer for streamer in streamer_list if streamer.lower().startswith(term)]
    return streamer_list

