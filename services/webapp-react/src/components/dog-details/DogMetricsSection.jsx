import PropTypes from 'prop-types';

function Metric({ label, value }) {
  return (
    <div className="dog-metric">
      <div className="dog-metric-icon" />
      <div className="dog-metric-text">
        <span className="metric-label">{label}</span>
        <span className="metric-value">{value}</span>
      </div>
    </div>
  );
}

Metric.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired
};

export function DogMetricsSection({ dog }) {
  const additionalMetrics = [
    dog.physical?.color && <Metric key="color" label="Color" value={dog.physical.color} />,
    dog.physical?.pattern && <Metric key="pattern" label="Pattern" value={dog.physical.pattern} />,
    // TODO: Add distinguishing marks when available in schema
    // dog.DistinguishingMarks && <Metric key="marks" label="Marks" value={dog.DistinguishingMarks} />,
  ].filter(Boolean);

  return (
    <>
      <div className="dog-metrics-row">
        <Metric label="Size" value={dog.physical?.sizeLabel || 'Unknown'} />
        <Metric label="Sex" value={dog.physical?.sex || 'Unknown'} />
        <Metric label="Weight" value={dog.physical?.weightLbs ? `${dog.physical.weightLbs} pounds` : 'Unknown'} />
        <Metric label="Age" value={dog.ageDisplay || 'Unknown'} />
      </div>
      {additionalMetrics.length > 0 && (
        <div className="dog-metrics-row">{additionalMetrics}</div>
      )}
    </>
  );
}

DogMetricsSection.propTypes = {
  dog: PropTypes.object.isRequired
};


