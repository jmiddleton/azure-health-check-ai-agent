

from typing import Any
import pandas as pd
import plotly.express as px

class PlotlyChartCreator:
    def __init__(self):
        pass

    @staticmethod
    def create_plotly(name:str, chart_type: str, data: list[dict]) -> Any:
        fig = None
        if chart_type == "line":
            fig = px.line(data_frame=data, x='timestamp', y="count", title=name)
        else:
            fig = px.bar(data_frame=data, x='timestamp', y="count", title=name)

        return fig