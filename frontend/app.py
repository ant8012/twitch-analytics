
import data

import dotenv
from st_aggrid import AgGrid, GridOptionsBuilder
import streamlit as st
from streamlit_echarts import st_echarts
from streamlit_searchbox import st_searchbox
import streamlit_shadcn_ui as ui

dotenv.load_dotenv()

st.set_page_config(layout="wide")

DISPLAY_TOP_VALUES = 8


def stream_metrics_cards(latest_stream_metrics):
    cols = st.columns(3)
    with cols[0]:
        ui.metric_card(
            title="Current Viewers",
            content=f"{latest_stream_metrics.iloc[0]['total_viewers']:,}",
            description="Number of active viewers",
            key="card1",
        )
    with cols[1]:
        ui.metric_card(
            title="Current Channels",
            content=f"{latest_stream_metrics.iloc[0]['total_streams']:,}",
            description="Number of live streams",
            key="card2",
        )
    with cols[2]:
        ui.metric_card(
            title="Current Games",
            content=f"{latest_stream_metrics.iloc[0]['unique_games']:,}",
            description="Number of unique games",
            key="card3",
        )

def stream_viewers_chart(live_viewers):
    options = {
            "title": {"text": "Current Viewers"},
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {
                    "type": "cross",
                    "label": {"backgroundColor": "#6a7985"},
                },
            },
            "legend": {"data": ["Viewers"]},
            "toolbox": {"feature": {"saveAsImage": {}}},
            "grid": {
                "left": "3%",
                "right": "4%",
                "bottom": "3%",
                "containLabel": True,
            },
            "xAxis": [
                {
                    "type": "category",
                    "boundaryGap": True,
                    "data": live_viewers["timestamp"].tolist(),
                }
            ],
            "yAxis": [{"type": "value"}],
            "series": [
                {
                    "name": "Viewers",
                    "type": "line",
                    "stack": "1",
                    "areaStyle": {},
                    "emphasis": {"focus": "series"},
                    "data": live_viewers["total_viewers"].tolist(),
                },
            ],
    }

    st_echarts(options=options, height="400px")

def top_games_chart(stream_metrics, top_games):
    top_games_total_hours_watched = 0
    top_games_values = []

    # The pie chart requires a specific format to display values. Get the
    # top 8 values to display
    for i in range(DISPLAY_TOP_VALUES):
        top_games_total_hours_watched += int(top_games.iloc[i]["Hours Watched"])
        top_games_values.append(
            {
                "value": int(top_games.iloc[i]["Hours Watched"]),
                "name": top_games.iloc[i]["Name"],
            }
        )

    # Assume the other category is total hours watched for the entire site
    # subtracted by total hours watched in the top 8
    top_games_values.append(
        {
            "value": int(stream_metrics.iloc[0]["hours_watched"])
            - int(top_games_total_hours_watched),
            "name": "Other",
        }
    )

    pie_chart_options = {
        "title": {"text": "Most Watched Games (Total Hours)", "subtext": "", "left": "center"},
        "tooltip": {"trigger": "item"},
        "series": [
            {
                "name": "Game",
                "type": "pie",
                "radius": "50%",
                "data": top_games_values,
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)",
                    }
                },
            }
        ],
    }

    events = {
        "legendselectchanged": "function(params) { return params.selected }",
    }

    gb = GridOptionsBuilder.from_dataframe(
        top_games[
            [
                "Name",
                "Hours Watched",
                "Highest # of Viewers",
                "Highest # of Streamers",
            ]
        ],
        resizable=True,
    )

    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_selection(selection_mode="single")
    grid_options = gb.build()

    cols = st.columns(2)
    with cols[0]:
        st.header(":video_game: Top Games")
        AgGrid(
            top_games,
            gridOptions=grid_options,
            height=500,
            width="100%",
            fit_columns_on_grid_load=True,
            key="Top Games Chart",
        )

    with cols[1]:
        st_echarts(
            options=pie_chart_options,
            events=events,
            height="600px",
            key="Top Games Pie Chart",
        )

def top_streamers_chart(stream_metrics, top_streamers):
    top_streamers_values = []
    current_viewers_top_streamers = 0

    # The pie chart requires a specific format to display values. Get the
    # top 8 values to display
    for i in range(DISPLAY_TOP_VALUES):
        current_viewers_top_streamers += int(
            top_streamers.iloc[i]["Hours Watched"]
        )
        top_streamers_values.append(
            {
                "value": int(top_streamers.iloc[i]["Hours Watched"]),
                "name": top_streamers.iloc[i]["Name"],
            }
        )

    top_streamers_values.append(
        {
            "value": int(stream_metrics.iloc[0]["hours_watched"])
            - int(current_viewers_top_streamers),
            "name": "Other",
        }
    )


    pie_chart_options = {
        "title": {"text": "Most Watched Streamers (Total Hours)", "subtext": "", "left": "center"},
        "tooltip": {"trigger": "item"},
        "series": [
            {
                "name": "Streamer",
                "type": "pie",
                "radius": "50%",
                "data": top_streamers_values,
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)",
                    }
                },
            }
        ],
    }

    events = {
        "legendselectchanged": "function(params) { return params.selected }",
    }

    gb = GridOptionsBuilder.from_dataframe(
        top_streamers[["Name", "Hours Watched", "Highest # of Viewers"]],
        resizable=True,
    )
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_selection(selection_mode="single")
    grid_options = gb.build()

    cols = st.columns(2)
    with cols[0]:
        st.header(":computer: Top Streamers")
        AgGrid(
            top_streamers,
            gridOptions=grid_options,
            height=500,
            width="100%",
            fit_columns_on_grid_load=True,
            key="Top streamer chart",
        )

    with cols[1]:
        st_echarts(
            options=pie_chart_options,
            events=events,
            height="600px",
            key="render_top_streamers",
        )

st.title(":speech_balloon: Twitch Metrics")
st.caption("Updated every 6 hours")

top_games = []
top_streamers = []
stream_metrics = []
live_viewers = []

with st.spinner(text="Loading this may take up to 30 seconds..."):
    latest_stream_metrics = data.get_latest_stream_metrics()

stream_metrics_cards(latest_stream_metrics)

with st.spinner(text="Loading this may take up to 30 seconds..."):
    live_viewers = data.get_viewers(None)

stream_viewers_chart(live_viewers)

@st.fragment
def _search_streamer_fragment():
    st.header(":mag: Search for a streamer")
    selected_value = st_searchbox(
        data.get_streamer_list,
        key="streamer_searchbox",
        placeholder="Enter a streamer, ex: Northernlion",
        rerun_scope="fragment",
    )
    if selected_value:
        viewers_for_streamer = data.get_viewers(selected_value)
        stream_viewers_chart(viewers_for_streamer)


_search_streamer_fragment()

st.header(":calendar: Timescale Selector")
timescale = ui.tabs(options=["Hour", "Day", "Week"], default_value="Hour", key="time_filter")

with st.spinner(text="Loading this may take up to 30 seconds..."):
    top_games = data.get_top_games(timescale)
    stream_metrics = data.get_stream_metrics(timescale)
    top_streamers = data.get_top_streamers(timescale)

top_games_chart(stream_metrics, top_games)

with st.spinner(text="Loading this may take up to 30 seconds..."):
    stream_metrics = data.get_stream_metrics(timescale)

top_streamers_chart(stream_metrics, top_streamers)
