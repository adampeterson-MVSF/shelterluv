import PropTypes from 'prop-types';
import './CompatibilityWarningsSection.css';

function formatWarningDate(dateString) {
  if (!dateString) return 'Unknown date';
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  } catch {
    return dateString;
  }
}

function getWarningSeverityIcon(severity) {
  switch (severity?.toLowerCase()) {
    case 'not recommended':
      return '🚫';
    case 'caution':
      return '⚠️';
    case 'unknown':
    default:
      return '❓';
  }
}

function getWarningSeverityColor(severity) {
  switch (severity?.toLowerCase()) {
    case 'not recommended':
      return '#e74c3c';
    case 'caution':
      return '#f39c12';
    case 'unknown':
    default:
      return '#95a5a6';
  }
}

function getWarningSeverityClass(severity) {
  switch (severity?.toLowerCase()) {
    case 'not recommended':
      return 'severity-high';
    case 'caution':
      return 'severity-medium';
    case 'unknown':
    default:
      return 'severity-unknown';
  }
}

function groupWarningsBySeverity(compatibilityWarnings) {
  return compatibilityWarnings.reduce((acc, warning) => {
    const severity = warning.severity?.toLowerCase() || 'unknown';
    if (!acc[severity]) {
      acc[severity] = [];
    }
    acc[severity].push(warning);
    return acc;
  }, {});
}

function renderWarningGroups(highSeverityWarnings, mediumSeverityWarnings, unknownSeverityWarnings) {
  return (
    <div className="warnings-content">
      {/* High severity warnings first */}
      {highSeverityWarnings.length > 0 && (
        <div className="warnings-group">
          <h3 className="warnings-group-title">🚫 Not Recommended</h3>
          <div className="warnings-list">
            {highSeverityWarnings.map((warning, index) => (
              <WarningCard
                key={`${warning.warning_type}-${warning.date_noted}-${index}`}
                warning={warning}
              />
            ))}
          </div>
        </div>
      )}

      {/* Medium severity warnings */}
      {mediumSeverityWarnings.length > 0 && (
        <div className="warnings-group">
          <h3 className="warnings-group-title">⚠️ Caution Required</h3>
          <div className="warnings-list">
            {mediumSeverityWarnings.map((warning, index) => (
              <WarningCard
                key={`${warning.warning_type}-${warning.date_noted}-${index}`}
                warning={warning}
              />
            ))}
          </div>
        </div>
      )}

      {/* Unknown severity warnings */}
      {unknownSeverityWarnings.length > 0 && (
        <div className="warnings-group">
          <h3 className="warnings-group-title">❓ Additional Notes</h3>
          <div className="warnings-list">
            {unknownSeverityWarnings.map((warning, index) => (
              <WarningCard
                key={`${warning.warning_type}-${warning.date_noted}-${index}`}
                warning={warning}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function WarningCard({ warning }) {
  const severityColor = getWarningSeverityColor(warning.severity);
  const severityClass = getWarningSeverityClass(warning.severity);

  return (
    <div className={`warning-card ${severityClass}`}>
      <div className="warning-header">
        <div className="warning-icon">
          {getWarningSeverityIcon(warning.severity)}
        </div>
        <div className="warning-title-section">
          <h4 className="warning-type">{warning.warning_type}</h4>
          <span
            className="warning-severity-badge"
            style={{ backgroundColor: severityColor }}
          >
            {warning.severity || 'Unknown'}
          </span>
        </div>
        <div className="warning-date">
          {formatWarningDate(warning.date_noted)}
        </div>
      </div>

      <div className="warning-content">
        {warning.details && (
          <div className="warning-details">
            <h5>Details</h5>
            <p>{warning.details}</p>
          </div>
        )}
      </div>
    </div>
  );
}

WarningCard.propTypes = {
  warning: PropTypes.shape({
    warning_type: PropTypes.string,
    severity: PropTypes.string,
    details: PropTypes.string,
    date_noted: PropTypes.string
  }).isRequired
};

function CompatibilityIntro() {
  return (
    <div className="compatibility-intro">
      <h3>🏡 Compatibility Information</h3>
      <p>
        Every dog has unique needs and preferences. This section highlights important
        compatibility considerations to ensure the best possible match for adoption.
      </p>
      <div className="compatibility-legend">
        <div className="legend-item">
          <span className="legend-icon">⚠️</span>
          <span className="legend-text">Caution - May require extra attention</span>
        </div>
        <div className="legend-item">
          <span className="legend-icon">🚫</span>
          <span className="legend-text">Not Recommended - May not be suitable</span>
        </div>
      </div>
    </div>
  );
}

export function CompatibilityWarningsSection({ compatibilityWarnings }) {
  if (!compatibilityWarnings || compatibilityWarnings.length === 0) {
    return null; // Don't show section if no warnings
  }

  const groupedWarnings = groupWarningsBySeverity(compatibilityWarnings);
  const highSeverityWarnings = groupedWarnings['not recommended'] || [];
  const mediumSeverityWarnings = groupedWarnings['caution'] || [];
  const unknownSeverityWarnings = groupedWarnings['unknown'] || [];

  return (
    <section className="compatibility-warnings-section">
      <h2 className="section-title">⚠️ Compatibility Warnings</h2>

      <CompatibilityIntro />

      {renderWarningGroups(highSeverityWarnings, mediumSeverityWarnings, unknownSeverityWarnings)}

      <div className="warnings-footer">
        <p>
          <strong>Important:</strong> These warnings are based on professional assessments
          and help ensure successful adoptions. Our team is here to discuss any concerns
          and provide guidance for the best possible outcome.
        </p>
      </div>
    </section>
  );
}

CompatibilityWarningsSection.propTypes = {
  compatibilityWarnings: PropTypes.arrayOf(
    PropTypes.shape({
      warning_type: PropTypes.string,
      severity: PropTypes.string,
      details: PropTypes.string,
      date_noted: PropTypes.string
    })
  )
};
