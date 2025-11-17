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
    dog.Color && <Metric key="color" label="Color" value={dog.Color} />,
    dog.Pattern && <Metric key="pattern" label="Pattern" value={dog.Pattern} />,
    dog.DistinguishingMarks && (
      <Metric key="marks" label="Marks" value={dog.DistinguishingMarks} />
    ),
    dog.AgeGroup && <Metric key="age-group" label="Age Group" value={dog.AgeGroup} />
  ].filter(Boolean);

  return (
    <>
      <div className="dog-metrics-row">
        <Metric label="Size" value={dog.Size || 'Unknown'} />
        <Metric label="Sex" value={dog.Gender || 'Unknown'} />
        <Metric label="Weight" value={dog.Weight ? `${dog.Weight} pounds` : 'Unknown'} />
        <Metric label="Age" value={dog.AgeDisplay || 'Unknown'} />
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


