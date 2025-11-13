"""Generate interactive HTML dashboard for sleep data visualization."""

import csv
import re
from pathlib import Path
from typing import Optional, Callable, Dict
import logging

try:
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    raise ImportError(
        "Dashboard generation requires plotly and pandas. "
        "Install with: pip install plotly pandas"
    )

logger = logging.getLogger(__name__)

# Template registry
TEMPLATES: Dict[str, Callable] = {}


def register_template(name: str):
    """Decorator to register a dashboard template."""

    def decorator(func: Callable) -> Callable:
        TEMPLATES[name] = func
        return func

    return decorator


def seconds_to_hours(seconds: float) -> float:
    """Convert seconds to hours."""
    return seconds / 3600.0


def load_sleep_data(csv_path: str) -> pd.DataFrame:
    """
    Load sleep data from CSV file.

    Args:
        csv_path: Path to CSV file.

    Returns:
        DataFrame with sleep data.
    """
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df


@register_template("default")
def create_default_dashboard(df: pd.DataFrame) -> go.Figure:
    """
    Create the default sleep data dashboard.

    Args:
        df: DataFrame with sleep data.

    Returns:
        Plotly figure object.
    """
    # Filter out naps to avoid polluting sleep analysis
    if "is_nap" in df.columns:
        original_count = len(df)
        df = df[df["is_nap"] == 0].copy()
        nap_count = original_count - len(df)
        if nap_count > 0:
            logger.info(f"Filtered out {nap_count} nap(s) from dashboard")
    else:
        # Fallback: filter by duration if is_nap column doesn't exist
        original_count = len(df)
        if "total_sleep_duration" in df.columns:
            df = df[df["total_sleep_duration"] >= 10800].copy()  # 3 hours = 10800 seconds
            nap_count = original_count - len(df)
            if nap_count > 0:
                logger.info(f"Filtered out {nap_count} nap(s) (sleep < 3h) from dashboard")

    if len(df) == 0:
        logger.warning("No non-nap sleep data available")
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No sleep data available (all records are naps)",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16),
        )
        return fig

    # Create subplots
    fig = make_subplots(
        rows=3,
        cols=2,
        subplot_titles=(
            "Total Sleep Duration",
            "Sleep Stages Breakdown",
            "Heart Rate Trends",
            "Heart Rate Variability",
            "Breathing Rate",
            "Time in Bed vs Sleep",
        ),
        specs=[
            [{"type": "scatter"}, {"type": "bar"}],
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "scatter"}],
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1,
    )

    # 1. Total Sleep Duration (hours)
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["total_sleep_duration"].apply(seconds_to_hours),
            mode="lines+markers",
            name="Sleep Duration",
            line=dict(color="#1f77b4", width=2),
            marker=dict(size=6),
        ),
        row=1,
        col=1,
    )

    # 2. Sleep Stages Breakdown (average stacked bar)
    if all(
        col in df.columns
        for col in [
            "deep_sleep_duration",
            "rem_sleep_duration",
            "light_sleep_duration",
        ]
    ):
        avg_deep = df["deep_sleep_duration"].mean() / 3600
        avg_rem = df["rem_sleep_duration"].mean() / 3600
        avg_light = df["light_sleep_duration"].mean() / 3600

        fig.add_trace(
            go.Bar(
                x=["Average"],
                y=[avg_deep],
                name="Deep Sleep",
                marker_color="#2ca02c",
            ),
            row=1,
            col=2,
        )
        fig.add_trace(
            go.Bar(
                x=["Average"],
                y=[avg_rem],
                name="REM Sleep",
                marker_color="#ff7f0e",
            ),
            row=1,
            col=2,
        )
        fig.add_trace(
            go.Bar(
                x=["Average"],
                y=[avg_light],
                name="Light Sleep",
                marker_color="#d62728",
            ),
            row=1,
            col=2,
        )

    # 3. Heart Rate Trends
    if "average_heart_rate" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["average_heart_rate"],
                mode="lines+markers",
                name="Avg Heart Rate",
                line=dict(color="#9467bd", width=2),
                marker=dict(size=5),
            ),
            row=2,
            col=1,
        )
        if "lowest_heart_rate" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["lowest_heart_rate"],
                    mode="lines+markers",
                    name="Lowest HR",
                    line=dict(color="#8c564b", width=1, dash="dash"),
                    marker=dict(size=4),
                ),
                row=2,
                col=1,
            )

    # 4. Heart Rate Variability
    if "average_hrv" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["average_hrv"],
                mode="lines+markers",
                name="HRV",
                line=dict(color="#e377c2", width=2),
                marker=dict(size=6),
            ),
            row=2,
            col=2,
        )

    # 5. Breathing Rate
    if "average_breath" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["average_breath"],
                mode="lines+markers",
                name="Breathing Rate",
                line=dict(color="#7f7f7f", width=2),
                marker=dict(size=5),
            ),
            row=3,
            col=1,
        )

    # 6. Time in Bed vs Sleep
    if "time_in_bed" in df.columns and "total_sleep_duration" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["time_in_bed"].apply(seconds_to_hours),
                mode="lines+markers",
                name="Time in Bed",
                line=dict(color="#bcbd22", width=2),
                marker=dict(size=5),
            ),
            row=3,
            col=2,
        )
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["total_sleep_duration"].apply(seconds_to_hours),
                mode="lines+markers",
                name="Sleep Duration",
                line=dict(color="#17becf", width=2),
                marker=dict(size=5),
            ),
            row=3,
            col=2,
        )

    # Update axes labels
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_xaxes(title_text="", row=1, col=2)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=2)
    fig.update_xaxes(title_text="Date", row=3, col=1)
    fig.update_xaxes(title_text="Date", row=3, col=2)

    fig.update_yaxes(title_text="Hours", row=1, col=1)
    fig.update_yaxes(title_text="Hours", row=1, col=2)
    fig.update_yaxes(title_text="BPM", row=2, col=1)
    fig.update_yaxes(title_text="ms", row=2, col=2)
    fig.update_yaxes(title_text="Breaths/min", row=3, col=1)
    fig.update_yaxes(title_text="Hours", row=3, col=2)

    # Update layout with modern styling
    fig.update_layout(
        title=dict(
            text="Sleep Data Dashboard",
            x=0.5,
            font=dict(size=28, color="#2d3748", family="Arial Black"),
        ),
        height=1200,
        showlegend=True,
        hovermode="x unified",
        template="plotly_white",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", size=12, color="#4a5568"),
        legend=dict(
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#e2e8f0",
            borderwidth=1,
            font=dict(size=11),
        ),
    )

    return fig


@register_template("deep_sleep")
def create_deep_sleep_dashboard(df: pd.DataFrame) -> go.Figure:
    """
    Create a deep sleep focused dashboard.

    Args:
        df: DataFrame with sleep data.

    Returns:
        Plotly figure object.
    """
    # Filter out naps to avoid polluting deep sleep analysis
    if "is_nap" in df.columns:
        original_count = len(df)
        df = df[df["is_nap"] == 0].copy()
        nap_count = original_count - len(df)
        if nap_count > 0:
            logger.info(f"Filtered out {nap_count} nap(s) from deep sleep analysis")
    else:
        # Fallback: filter by duration if is_nap column doesn't exist
        # (for backward compatibility with old CSV files)
        original_count = len(df)
        if "total_sleep_duration" in df.columns:
            df = df[df["total_sleep_duration"] >= 10800].copy()  # 3 hours = 10800 seconds
            nap_count = original_count - len(df)
            if nap_count > 0:
                logger.info(
                    f"Filtered out {nap_count} nap(s) (sleep < 3h) from deep sleep analysis"
                )

    if len(df) == 0:
        logger.warning("No non-nap sleep data available for deep sleep analysis")
        return create_default_dashboard(df)

    # Create subplots focused on deep sleep analysis
    fig = make_subplots(
        rows=3,
        cols=2,
        subplot_titles=(
            "Deep Sleep Duration Trend",
            "Deep Sleep Percentage of Total Sleep",
            "Deep Sleep vs Other Stages",
            "Deep Sleep vs Heart Rate",
            "Deep Sleep vs HRV",
            "Deep Sleep Efficiency (Deep Sleep / Time in Bed)",
        ),
        specs=[
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "bar"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "scatter"}],
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1,
    )

    if "deep_sleep_duration" not in df.columns:
        logger.warning("Deep sleep data not available")
        return create_default_dashboard(df)

    # Calculate deep sleep in hours
    df["deep_sleep_hours"] = df["deep_sleep_duration"].apply(seconds_to_hours)
    df["total_sleep_hours"] = df["total_sleep_duration"].apply(seconds_to_hours)
    df["deep_sleep_percentage"] = (
        df["deep_sleep_duration"] / df["total_sleep_duration"] * 100
    )
    df["deep_sleep_efficiency"] = (
        df["deep_sleep_duration"] / df["time_in_bed"] * 100
    )

    # 1. Deep Sleep Duration Trend
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["deep_sleep_hours"],
            mode="lines+markers",
            name="Deep Sleep",
            line=dict(color="#2ca02c", width=3),
            marker=dict(size=8),
            fill="tozeroy",
            fillcolor="rgba(44, 160, 44, 0.2)",
        ),
        row=1,
        col=1,
    )

    # Add average line
    avg_deep = df["deep_sleep_hours"].mean()
    fig.add_hline(
        y=avg_deep,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Avg: {avg_deep:.2f}h",
        row=1,
        col=1,
    )

    # 2. Deep Sleep Percentage
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["deep_sleep_percentage"],
            mode="lines+markers",
            name="Deep Sleep %",
            line=dict(color="#1f77b4", width=2),
            marker=dict(size=6),
        ),
        row=1,
        col=2,
    )

    # Add recommended range (15-20% for adults)
    fig.add_hrect(
        y0=15,
        y1=20,
        fillcolor="rgba(0, 255, 0, 0.1)",
        layer="below",
        line_width=0,
        row=1,
        col=2,
    )
    fig.add_annotation(
        text="Recommended: 15-20%",
        xref="x2",
        yref="y2",
        x=df["date"].iloc[len(df) // 2],
        y=17.5,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        row=1,
        col=2,
    )

    # 3. Deep Sleep vs Other Stages (stacked area)
    if all(
        col in df.columns
        for col in ["rem_sleep_duration", "light_sleep_duration"]
    ):
        df["rem_hours"] = df["rem_sleep_duration"].apply(seconds_to_hours)
        df["light_hours"] = df["light_sleep_duration"].apply(seconds_to_hours)

        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["deep_sleep_hours"],
                name="Deep Sleep",
                marker_color="#2ca02c",
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["rem_hours"],
                name="REM Sleep",
                marker_color="#ff7f0e",
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["light_hours"],
                name="Light Sleep",
                marker_color="#d62728",
            ),
            row=2,
            col=1,
        )

    # 4. Deep Sleep vs Heart Rate
    if "average_heart_rate" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["deep_sleep_hours"],
                y=df["average_heart_rate"],
                mode="markers",
                name="Deep Sleep vs HR",
                marker=dict(
                    size=8,
                    color=df["deep_sleep_hours"],
                    colorscale="Viridis",
                    showscale=True,
                    colorbar=dict(title="Deep Sleep (h)", x=1.15),
                ),
                text=df["date"].dt.strftime("%Y-%m-%d"),
                hovertemplate="<b>%{text}</b><br>"
                "Deep Sleep: %{x:.2f}h<br>"
                "Heart Rate: %{y:.1f} BPM<extra></extra>",
            ),
            row=2,
            col=2,
        )

    # 5. Deep Sleep vs HRV
    if "average_hrv" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["deep_sleep_hours"],
                y=df["average_hrv"],
                mode="markers",
                name="Deep Sleep vs HRV",
                marker=dict(
                    size=8,
                    color=df["deep_sleep_hours"],
                    colorscale="Plasma",
                    showscale=True,
                    colorbar=dict(title="Deep Sleep (h)", x=1.15),
                ),
                text=df["date"].dt.strftime("%Y-%m-%d"),
                hovertemplate="<b>%{text}</b><br>"
                "Deep Sleep: %{x:.2f}h<br>"
                "HRV: %{y:.1f} ms<extra></extra>",
            ),
            row=3,
            col=1,
        )

    # 6. Deep Sleep Efficiency
    if "time_in_bed" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["deep_sleep_efficiency"],
                mode="lines+markers",
                name="Deep Sleep Efficiency",
                line=dict(color="#9467bd", width=2),
                marker=dict(size=6),
                fill="tozeroy",
                fillcolor="rgba(148, 103, 189, 0.2)",
            ),
            row=3,
            col=2,
        )

    # Update axes labels
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=1, col=2)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_xaxes(title_text="Deep Sleep (hours)", row=2, col=2)
    fig.update_xaxes(title_text="Deep Sleep (hours)", row=3, col=1)
    fig.update_xaxes(title_text="Date", row=3, col=2)

    fig.update_yaxes(title_text="Hours", row=1, col=1)
    fig.update_yaxes(title_text="Percentage (%)", row=1, col=2)
    fig.update_yaxes(title_text="Hours", row=2, col=1)
    fig.update_yaxes(title_text="BPM", row=2, col=2)
    fig.update_yaxes(title_text="HRV (ms)", row=3, col=1)
    fig.update_yaxes(title_text="Efficiency (%)", row=3, col=2)

    # Update layout with modern styling
    fig.update_layout(
        title=dict(
            text="Deep Sleep Analysis Dashboard",
            x=0.5,
            font=dict(size=28, color="#2d3748", family="Arial Black"),
        ),
        height=1200,
        showlegend=True,
        hovermode="closest",
        template="plotly_white",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", size=12, color="#4a5568"),
        legend=dict(
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#e2e8f0",
            borderwidth=1,
            font=dict(size=11),
        ),
    )

    return fig


def _add_breadcrumb_navigation(html_content: str, current_template: str) -> str:
    """
    Add breadcrumb navigation to dashboard HTML.

    Args:
        html_content: Original HTML content from Plotly.
        current_template: Name of the current dashboard template.

    Returns:
        HTML content with breadcrumb navigation added.
    """
    template_names = {
        "default": "Default Dashboard",
        "deep_sleep": "Deep Sleep Dashboard",
    }

    # Build breadcrumb HTML
    breadcrumb_items = []
    for template_name in TEMPLATES.keys():
        if template_name == current_template:
            breadcrumb_items.append(
                f'<span class="breadcrumb-current">{template_names.get(template_name, template_name)}</span>'
            )
        else:
            filename = f"{template_name}_dashboard.html"
            breadcrumb_items.append(
                f'<a href="{filename}" class="breadcrumb-link">{template_names.get(template_name, template_name)}</a>'
            )

    breadcrumb_html = f"""
    <div class="breadcrumb-nav">
        <div class="breadcrumb-container">
            {' | '.join(breadcrumb_items)}
        </div>
    </div>
    """

    # Insert breadcrumb after opening body tag
    if "<body>" in html_content:
        html_content = html_content.replace("<body>", f"<body>{breadcrumb_html}")
    elif "<body " in html_content:
        html_content = re.sub(
            r"(<body[^>]*>)", r"\1" + breadcrumb_html, html_content, count=1
        )

    return html_content


def _add_date_filter_and_styling(html_content: str, df: pd.DataFrame) -> str:
    """
    Add date filter controls and modern styling to dashboard HTML.

    Args:
        html_content: Original HTML content from Plotly.
        df: DataFrame with sleep data (for date range).

    Returns:
        HTML content with date filters and modern styling added.
    """
    if len(df) == 0:
        return html_content

    min_date = df["date"].min().strftime("%Y-%m-%d")
    max_date = df["date"].max().strftime("%Y-%m-%d")

    filter_html = f"""
    <div class="dashboard-header">
        <div class="date-filter-container">
            <label for="start-date" class="filter-label">Start Date:</label>
            <input type="date" id="start-date" class="date-input" value="{min_date}" min="{min_date}" max="{max_date}">
            <label for="end-date" class="filter-label">End Date:</label>
            <input type="date" id="end-date" class="date-input" value="{max_date}" min="{min_date}" max="{max_date}">
            <button id="apply-filter" class="filter-button">Apply Filter</button>
            <button id="reset-filter" class="filter-button filter-button-secondary">Reset</button>
        </div>
        <div class="filter-info" id="filter-info"></div>
    </div>
    """

    modern_styles = """
    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }

        .breadcrumb-nav {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 16px 24px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .breadcrumb-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .breadcrumb-link {
            color: #667eea;
            text-decoration: none;
            padding: 6px 12px;
            border-radius: 6px;
            transition: all 0.2s ease;
            font-weight: 500;
        }

        .breadcrumb-link:hover {
            background-color: #f0f0f0;
            text-decoration: none;
            transform: translateY(-1px);
        }

        .breadcrumb-current {
            color: #764ba2;
            font-weight: 600;
            padding: 6px 12px;
        }

        .dashboard-header {
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(10px);
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .date-filter-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            gap: 16px;
            flex-wrap: wrap;
        }

        .filter-label {
            font-weight: 600;
            color: #333;
            font-size: 14px;
        }

        .date-input {
            padding: 10px 14px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.2s ease;
            background: white;
            color: #333;
        }

        .date-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .filter-button {
            padding: 10px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        }

        .filter-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .filter-button:active {
            transform: translateY(0);
        }

        .filter-button-secondary {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            box-shadow: 0 2px 8px rgba(245, 87, 108, 0.3);
        }

        .filter-button-secondary:hover {
            box-shadow: 0 4px 12px rgba(245, 87, 108, 0.4);
        }

        .filter-info {
            max-width: 1400px;
            margin: 12px auto 0;
            padding: 8px 16px;
            background: rgba(102, 126, 234, 0.1);
            border-radius: 6px;
            font-size: 13px;
            color: #667eea;
            display: none;
        }

        .filter-info.active {
            display: block;
        }

        .plotly-graph-div {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
            margin: 24px auto;
            padding: 20px;
            max-width: 1400px;
        }

        .js-plotly-plot {
            border-radius: 8px;
        }
    </style>
    """

    filter_script = """
    <script>
        (function() {
            const startDateInput = document.getElementById('start-date');
            const endDateInput = document.getElementById('end-date');
            const applyButton = document.getElementById('apply-filter');
            const resetButton = document.getElementById('reset-filter');
            const filterInfo = document.getElementById('filter-info');

            if (!startDateInput || !endDateInput) return;

            const originalMinDate = startDateInput.min;
            const originalMaxDate = startDateInput.max;

            // Store original data for each graph
            const originalData = new Map();

            function storeOriginalData() {
                if (!window.Plotly) return;

                const graphDivs = document.querySelectorAll('.js-plotly-plot');
                graphDivs.forEach((plotDiv, idx) => {
                    if (!originalData.has(idx)) {
                        const graphData = window.Plotly.d3.select(plotDiv).datum();
                        if (graphData && graphData.data) {
                            // Deep clone the data
                            const cloned = JSON.parse(JSON.stringify(graphData.data));
                            originalData.set(idx, cloned);
                        }
                    }
                });
            }

            // Store data after page loads
            window.addEventListener('load', () => {
                setTimeout(storeOriginalData, 500);
            });

            function updateFilterInfo() {
                const start = startDateInput.value;
                const end = endDateInput.value;
                if (start !== originalMinDate || end !== originalMaxDate) {
                    filterInfo.textContent = `Filtered: ${start} to ${end}`;
                    filterInfo.classList.add('active');
                } else {
                    filterInfo.classList.remove('active');
                }
            }

            function applyDateFilter() {
                const startDate = new Date(startDateInput.value + 'T00:00:00');
                const endDate = new Date(endDateInput.value + 'T23:59:59');

                if (!window.Plotly) {
                    console.error('Plotly not available');
                    return;
                }

                const graphDivs = document.querySelectorAll('.js-plotly-plot');

                graphDivs.forEach((plotDiv, graphIdx) => {
                    const originalTraces = originalData.get(graphIdx);
                    if (!originalTraces) {
                        // Fallback: try to get current data
                        const graphData = window.Plotly.d3.select(plotDiv).datum();
                        if (!graphData || !graphData.data) return;
                        applyFilterToTraces(plotDiv, graphData.data, startDate, endDate);
                    } else {
                        applyFilterToTraces(plotDiv, originalTraces, startDate, endDate);
                    }
                });

                updateFilterInfo();
            }

            function applyFilterToTraces(plotDiv, traces, startDate, endDate) {
                traces.forEach((trace, traceIdx) => {
                    if (!trace.x || !Array.isArray(trace.x)) return;

                    const filteredX = [];
                    const filteredY = [];
                    const filteredIndices = [];

                    trace.x.forEach((xVal, i) => {
                        let date;
                        if (typeof xVal === 'string') {
                            date = new Date(xVal);
                        } else if (xVal instanceof Date) {
                            date = xVal;
                        } else {
                            return;
                        }

                        if (date >= startDate && date <= endDate) {
                            filteredX.push(xVal);
                            if (trace.y && trace.y[i] !== undefined) {
                                filteredY.push(trace.y[i]);
                            }
                            filteredIndices.push(i);
                        }
                    });

                    if (filteredX.length > 0) {
                        const update = { x: [filteredX] };
                        if (filteredY.length > 0) {
                            update.y = [filteredY];
                        }

                        // Filter other array properties
                        Object.keys(trace).forEach(key => {
                            if (key !== 'x' && key !== 'y' &&
                                Array.isArray(trace[key]) &&
                                trace[key].length === trace.x.length) {
                                const filtered = filteredIndices.map(idx => trace[key][idx]);
                                update[key] = [filtered];
                            }
                        });

                        window.Plotly.restyle(plotDiv, update, traceIdx);
                    } else {
                        // Hide trace if no data in range
                        window.Plotly.restyle(plotDiv, { visible: ['legendonly'] }, traceIdx);
                    }
                });
            }

            function resetFilter() {
                startDateInput.value = originalMinDate;
                endDateInput.value = originalMaxDate;

                // Reload the page to reset all charts
                location.reload();
            }

            applyButton.addEventListener('click', applyDateFilter);
            resetButton.addEventListener('click', resetFilter);

            // Update info on date change
            startDateInput.addEventListener('change', updateFilterInfo);
            endDateInput.addEventListener('change', updateFilterInfo);
        })();
    </script>
    """

    # Insert filter and styles after breadcrumb
    if "<body>" in html_content:
        html_content = html_content.replace(
            "<body>", f"<body>{modern_styles}{filter_html}{filter_script}"
        )
    elif "<body " in html_content:
        html_content = re.sub(
            r"(<body[^>]*>)",
            r"\1" + modern_styles + filter_html + filter_script,
            html_content,
            count=1,
        )

    return html_content


def create_dashboard(
    csv_path: str,
    output_path: Optional[str] = None,
    template: str = "default",
) -> str:
    """
    Create an interactive HTML dashboard from sleep data CSV.

    Args:
        csv_path: Path to input CSV file with sleep data.
        output_path: Path for output HTML file. If None, defaults to `{template}_dashboard.html` in the `dashboards/` subdirectory.
        template: Dashboard template to use. Available: 'default', 'deep_sleep'. Defaults to 'default'.

    Returns:
        Path to generated HTML dashboard file.
    """
    if template not in TEMPLATES:
        available = ", ".join(TEMPLATES.keys())
        raise ValueError(
            f"Unknown template '{template}'. Available templates: {available}"
        )

    if output_path is None:
        csv_file = Path(csv_path)
        # Always use exports/dashboards/ regardless of CSV location
        # If CSV is in exports/data/, go up one level to exports/
        if csv_file.parent.name == "data":
            base_dir = csv_file.parent.parent
        else:
            base_dir = csv_file.parent
        dashboards_dir = base_dir / "dashboards"
        dashboards_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(dashboards_dir / f"{template}_dashboard.html")

    logger.info(f"Loading sleep data from {csv_path}")
    df = load_sleep_data(csv_path)

    if len(df) == 0:
        logger.warning("No data to visualize")
        return output_path

    logger.info(f"Creating dashboard with {len(df)} records using '{template}' template")

    # Get template function and create dashboard
    template_func = TEMPLATES[template]
    fig = template_func(df)

    # Save to HTML
    logger.info(f"Saving dashboard to {output_path}")
    fig.write_html(output_path)

    # Add breadcrumb navigation, date filters, and modern styling
    with open(output_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    html_content = _add_breadcrumb_navigation(html_content, template)
    html_content = _add_date_filter_and_styling(html_content, df)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path


def create_all_dashboards(csv_path: str) -> list[str]:
    """
    Create all available dashboard templates.

    Args:
        csv_path: Path to input CSV file with sleep data.

    Returns:
        List of paths to generated HTML dashboard files.
    """
    generated_paths = []
    for template_name in TEMPLATES.keys():
        try:
            path = create_dashboard(csv_path, template=template_name)
            generated_paths.append(path)
        except Exception as e:
            logger.error(f"Failed to generate {template_name} dashboard: {e}")

    return generated_paths


def list_templates() -> list[str]:
    """Return list of available dashboard templates."""
    return list(TEMPLATES.keys())
