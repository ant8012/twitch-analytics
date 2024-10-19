
import pandas as pd
import streamlit as st

@st.cache_data
def get_top_games_hour(_cursor):
    _cursor.columns(schema_name="twitch_test", table_name="top_games_hour")
    _cursor.execute("SELECT * FROM top_games_hour LIMIT 100")
    rows = _cursor.fetchall()
    column_names = [desc[0] for desc in _cursor.description]
    return pd.DataFrame(rows, columns=column_names)


@st.cache_data
def get_top_games_day(cursor):
    cursor.columns(schema_name="twitch_test", table_name="top_games_day")
    cursor.execute("SELECT * FROM top_games_day LIMIT 100")
    rows = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    return pd.DataFrame(rows, columns=column_names)


@st.cache_data
def get_top_games_week(cursor):
    cursor.columns(schema_name="twitch_test", table_name="top_games_week")
    cursor.execute("SELECT * FROM top_games_week LIMIT 100")
    rows = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    return pd.DataFrame(rows, columns=column_names)


@st.cache_data
def get_top_games(_cursor, timescale):
    table_name = ""
    if timescale == "Hour":
        table_name = "top_games_hour"
    elif timescale == "Day":
        table_name = "top_games_day"
    elif timescale == "Week":
        table_name = "top_games_week"

    _cursor.columns(schema_name="twitch_test", table_name=table_name)
    _cursor.execute(f"SELECT * FROM {table_name} ORDER BY hours_watched DESC LIMIT 100")

    rows = _cursor.fetchall()
    column_names = [desc[0] for desc in _cursor.description]
    df = pd.DataFrame(rows, columns=column_names)
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


@st.cache_data
def get_top_streamers(_cursor, timescale):
    table_name = ""
    if timescale == "Hour":
        table_name = "top_streamers_hour"
    elif timescale == "Day":
        table_name = "top_streamers_day"
    elif timescale == "Week":
        table_name = "top_streamers_week"

    _cursor.columns(schema_name="twitch_test", table_name=table_name)
    _cursor.execute(f"SELECT * FROM {table_name} ORDER BY hours_watched DESC LIMIT 100")

    rows = _cursor.fetchall()
    column_names = [desc[0] for desc in _cursor.description]
    df = pd.DataFrame(rows, columns=column_names)
    df.rename(
        columns={
            "user_name": "Name",
            "hours_watched": "Hours Watched",
            "max_viewers": "Highest # of Viewers",
        },
        inplace=True,
    )
    return df


@st.cache_data
def get_stream_metrics(_cursor, timescale):
    table_name = ""
    if timescale == "Hour":
        table_name = "latest_stream_metrics_hour"
    elif timescale == "Day":
        table_name = "latest_stream_metrics_day"
    elif timescale == "Week":
        table_name = "latest_stream_metrics_week"

    _cursor.columns(schema_name="twitch_test", table_name=table_name)
    _cursor.execute(f"SELECT * FROM {table_name}")

    rows = _cursor.fetchall()
    column_names = [desc[0] for desc in _cursor.description]
    df = pd.DataFrame(rows, columns=column_names)
    return df


@st.cache_data
def get_streamer_list(_cursor):
    _cursor.columns(schema_name="twitch_test", table_name="silver_twitch_streams")
    _cursor.execute("SELECT DISTINCT user_name from silver_twitch_streams")

    rows = _cursor.fetchall()
    column_names = [desc[0] for desc in _cursor.description]
    df = pd.DataFrame(rows, columns=column_names)
    return df


@st.cache_data
def get_viewers(_cursor):
    _cursor.columns(schema_name="twitch_test", table_name="silver_twitch_streams")
    _cursor.execute(
        "SELECT date_format(timestamp, 'MMM d HH:mm') as timestamp, SUM(viewer_count) as total_viewers from silver_twitch_streams WHERE timestamp >= CURRENT_TIMESTAMP() - INTERVAL 7 DAY group by timestamp order by timestamp ASC"
    )

    rows = _cursor.fetchall()
    column_names = [desc[0] for desc in _cursor.description]
    df = pd.DataFrame(rows, columns=column_names)
    return df


@st.cache_data
def get_latest_stream_metrics(_cursor):
    _cursor.columns(schema_name="twitch_test", table_name="latest_stream_metrics")
    _cursor.execute("SELECT * FROM latest_stream_metrics")

    rows = _cursor.fetchall()
    column_names = [desc[0] for desc in _cursor.description]

    return pd.DataFrame(rows, columns=column_names)