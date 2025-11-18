import { useMemo } from 'react';
import PropTypes from 'prop-types';
import './WeightHistorySection.css';

function formatWeightDate(dateString) {
  if (!dateString) return 'Unknown';
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: '2-digit'
    });
  } catch {
    return dateString;
  }
}

function processWeightData(weightData) {
  if (!weightData || weightData.length === 0) return { chartData: [], minWeight: 0, maxWeight: 0, chartHeight: 0 };

  // Convert weights to numbers and sort by date
  const processed = weightData
    .map(item => ({
      ...item,
      weightNum: parseFloat(item.weight) || 0,
      dateObj: new Date(item.date)
    }))
    .filter(item => item.weightNum > 0)
    .sort((a, b) => a.dateObj - b.dateObj);

  if (processed.length === 0) return { chartData: [], minWeight: 0, maxWeight: 0, chartHeight: 0 };

  const minWeight = Math.min(...processed.map(d => d.weightNum));
  const maxWeight = Math.max(...processed.map(d => d.weightNum));
  const range = maxWeight - minWeight || 1;
  const chartHeight = 120; // pixels

  const chartData = processed.map(item => ({
    ...item,
    y: ((item.weightNum - minWeight) / range) * (chartHeight - 20) + 10, // 10px margin
    formattedDate: formatWeightDate(item.date)
  }));

  return { chartData, minWeight, maxWeight, chartHeight };
}

function WeightChart({ weightData }) {
  const { chartData, minWeight, maxWeight, chartHeight } = useMemo(() =>
    processWeightData(weightData), [weightData]
  );

  if (!chartData || chartData.length === 0) {
    return (
      <div className="weight-chart-placeholder">
        <p>No weight data available for charting</p>
      </div>
    );
  }

  const chartWidth = Math.max(300, chartData.length * 60); // Minimum width, 60px per point

  return (
    <div className="weight-chart-container">
      <div className="weight-chart-header">
        <h4>Weight Trend</h4>
        <div className="weight-range">
          <span className="weight-min">{minWeight.toFixed(1)} {chartData[0]?.unit || 'lbs'}</span>
          <span className="weight-max">{maxWeight.toFixed(1)} {chartData[0]?.unit || 'lbs'}</span>
        </div>
      </div>

      <div className="weight-chart" style={{ height: chartHeight + 40 }}>
        <svg width={chartWidth} height={chartHeight + 40} className="weight-chart-svg">
          {/* Grid lines */}
          <line x1="0" y1={chartHeight - 10} x2={chartWidth} y2={chartHeight - 10} stroke="#e1e8ed" strokeWidth="1" />
          <line x1="0" y1={chartHeight / 2} x2={chartWidth} y2={chartHeight / 2} stroke="#f1f3f4" strokeWidth="1" />

          {/* Data line */}
          {chartData.map((point, index) => {
            if (index === 0) return null;
            const prevPoint = chartData[index - 1];
            return (
              <line
                key={`line-${index}`}
                x1={(index - 1) * (chartWidth / Math.max(chartData.length - 1, 1))}
                y1={chartHeight - prevPoint.y}
                x2={index * (chartWidth / Math.max(chartData.length - 1, 1))}
                y2={chartHeight - point.y}
                stroke="#3498db"
                strokeWidth="2"
              />
            );
          })}

          {/* Data points */}
          {chartData.map((point, index) => (
            <circle
              key={`point-${index}`}
              cx={index * (chartWidth / Math.max(chartData.length - 1, 1))}
              cy={chartHeight - point.y}
              r="4"
              fill="#3498db"
              stroke="white"
              strokeWidth="2"
            >
              <title>{`${point.weight} ${point.unit} on ${point.formattedDate}`}</title>
            </circle>
          ))}
        </svg>

        {/* Date labels */}
        <div className="weight-chart-labels">
          {chartData.map((point, index) => (
            <div
              key={`label-${index}`}
              className="weight-chart-label"
              style={{
                left: `${index * (100 / Math.max(chartData.length - 1, 1))}%`,
                transform: 'translateX(-50%)'
              }}
            >
              {point.formattedDate}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

WeightChart.propTypes = {
  weightData: PropTypes.arrayOf(
    PropTypes.shape({
      weight: PropTypes.string,
      date: PropTypes.string,
      unit: PropTypes.oneOf(['kg', 'lbs'])
    })
  )
};

function WeightHistoryTable({ weightData }) {
  if (!weightData || weightData.length === 0) return null;

  const sortedData = [...weightData].sort((a, b) => {
    if (!a.date && !b.date) return 0;
    if (!a.date) return 1;
    if (!b.date) return -1;
    return new Date(b.date) - new Date(a.date);
  });

  return (
    <div className="weight-history-table">
      <h4>Weight Measurements</h4>
      <div className="weight-table-container">
        <table className="weight-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Weight</th>
              <th>Unit</th>
            </tr>
          </thead>
          <tbody>
            {sortedData.map((entry, index) => (
              <tr key={`${entry.date}-${entry.weight}-${index}`}>
                <td>{formatWeightDate(entry.date)}</td>
                <td className="weight-value">{entry.weight}</td>
                <td>{entry.unit || 'lbs'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

WeightHistoryTable.propTypes = {
  weightData: PropTypes.arrayOf(
    PropTypes.shape({
      weight: PropTypes.string,
      date: PropTypes.string,
      unit: PropTypes.oneOf(['kg', 'lbs'])
    })
  )
};

export function WeightHistorySection({ weightHistory }) {
  if (!weightHistory || weightHistory.length === 0) {
    return (
      <section className="weight-history-section">
        <h2 className="section-title">⚖️ Weight History</h2>
        <div className="no-data-message">
          <p>No weight history available for this dog.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="weight-history-section">
      <h2 className="section-title">⚖️ Weight History</h2>
      <div className="weight-history-content">
        <WeightChart weightData={weightHistory} />
        <WeightHistoryTable weightData={weightHistory} />
      </div>
    </section>
  );
}

WeightHistorySection.propTypes = {
  weightHistory: PropTypes.arrayOf(
    PropTypes.shape({
      weight: PropTypes.string,
      date: PropTypes.string,
      unit: PropTypes.oneOf(['kg', 'lbs'])
    })
  )
};
