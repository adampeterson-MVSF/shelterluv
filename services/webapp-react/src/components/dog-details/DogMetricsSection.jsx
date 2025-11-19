import PropTypes from 'prop-types';
import { PawPrint, Scale, Clock, Mars, Venus, HelpCircle } from 'lucide-react';

// Helper to select icon based on label or value
function getIcon(label, value) {
  if (label === 'Size') return <PawPrint color="#F4B400" />;
  if (label === 'Weight') return <Scale color="#F4B400" />;
  if (label === 'Age') return <Clock color="#F4B400" />;
  if (label === 'Sex') {
    if (value === 'Male') return <Mars color="#F4B400" />;
    if (value === 'Female') return <Venus color="#F4B400" />;
  }
  return <HelpCircle color="#F4B400" />;
}

function Metric({ label, value }) {
  return (
    <div className="dog-metric">
      <div className="dog-metric-icon">
        {getIcon(label, value)}
      </div>
      <div className="dog-metric-text">
        <span className="metric-value" style={{color: '#F4B400', fontSize: '1.5rem'}}>{value}</span>
        <span className="metric-label">{label}</span>
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


