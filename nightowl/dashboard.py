"""Generate interactive HTML dashboard for sleep data visualization."""

import csv
from pathlib import Path
from typing import Optional
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


def create_dashboard(csv_path: str, output_path: Optional[str] = None) -> str:
    """
    Create an interactive HTML dashboard from sleep data CSV.

    Args:
        csv_path: Path to input CSV file with sleep data.
        output_path: Path for output HTML file. If None, defaults to `nightowl_dashboard.html` in the same directory as csv_path.

    Returns:
        Path to generated HTML dashboard file.
    """
    if output_path is None:
        csv_file = Path(csv_path)
        output_path = str(csv_file.parent / "nightowl_dashboard.html")

    logger.info(f"Loading sleep data from {csv_path}")
    df = load_sleep_data(csv_path)

    if len(df) == 0:
        logger.warning("No data to visualize")
        return output_path

    logger.info(f"Creating dashboard with {len(df)} records")

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

    # Update layout
    fig.update_layout(
        title=dict(
            text="Sleep Data Dashboard",
            x=0.5,
            font=dict(size=24),
        ),
        height=1200,
        showlegend=True,
        hovermode="x unified",
        template="plotly_white",
    )

    # Save to HTML
    logger.info(f"Saving dashboard to {output_path}")
    fig.write_html(output_path)

    return output_path
