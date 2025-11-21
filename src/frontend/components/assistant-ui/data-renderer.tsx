"use client";

import type { FC } from "react";
import dynamic from "next/dynamic";

// react-plotly.js works only in the browser; load dynamically
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });
const PlotAny: any = Plot;

type Props = {
  name?: string;
  data?: any;
};

export const DataRenderer: FC<Props> = ({ name, data }) => {
  if (!data) return null;

  // If the model returned a full Plotly spec, use it directly
  if (data.plotly && (data.plotly.data || data.plotly.layout)) {
    // @ts-ignore allow unknown props from Plotly
    return <PlotAny data={data.plotly.data} layout={data.plotly.layout || {}} style={{ width: "100%" }} useResizeHandler />;
  }

  // Only render chart if data is valid, has type 'appInsights', and a timeseries array
  if (data.type === "appInsights" && Array.isArray(data.timeseries) && data.timeseries.length > 0) {
    const timeseries: Array<{ timestamp?: string; time?: string; count?: number; value?: number }> = data.timeseries;
    const x = timeseries.map((point) => point.timestamp || point.time || "");
    const y = timeseries.map((point) => point.count ?? point.value ?? 0);

    const chartData = [
      {
        x,
        y,
        type: "scatter" as const,
        mode: "lines+markers" as const,
        marker: { color: "#0078d4" },
      },
    ];

    const layout = {
      autosize: true,
      margin: { t: 20, r: 20, b: 40, l: 40 },
      xaxis: { title: "Timestamp" },
      yaxis: { title: "Count" },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { family: "inherit" },
    };

    return (
      <div data-chart-renderer>
        {/* @ts-ignore: Plotly types */}
        <Plot data={chartData} layout={layout} config={{ displayModeBar: false }} style={{ width: "100%", height: "300px" }} />
      </div>
    );
  }

  // Fallback: render nothing (do not show raw JSON)
  return null;
};

export default DataRenderer;
