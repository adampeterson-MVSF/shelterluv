import PropTypes from 'prop-types';
import { useAuth } from '../../contexts/AuthContext';
import './BehavioralAssessmentsSection.css';

function formatAssessmentDate(dateString) {
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

function getAssessmentTypeIcon(assessmentType) {
  const iconMap = {
    'Initial Evaluation': '🔍',
    'Follow-up': '📝',
    'Training Assessment': '🎓',
    'Adoption Readiness': '🏡',
    'Behavior Plan Review': '📋'
  };
  return iconMap[assessmentType] || '🧠';
}

function AssessmentResults({ results }) {
  if (!results || typeof results !== 'object') return null;

  // Handle both string and object results
  if (typeof results === 'string') {
    return (
      <div className="assessment-results-text">
        <p>{results}</p>
      </div>
    );
  }

  // Handle structured results object
  const resultEntries = Object.entries(results);

  return (
    <div className="assessment-results-structured">
      <h5>Assessment Results</h5>
      <div className="results-grid">
        {resultEntries.map(([key, value]) => (
          <div key={key} className="result-item">
            <span className="result-label">{key.replace(/([A-Z])/g, ' $1').toLowerCase()}:</span>
            <span className="result-value">{String(value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

AssessmentResults.propTypes = {
  results: PropTypes.oneOfType([PropTypes.string, PropTypes.object])
};

function BehavioralAssessmentCard({ assessment }) {
  return (
    <div className="behavioral-assessment-card">
      <div className="assessment-header">
        <div className="assessment-type">
          <span className="assessment-icon">{getAssessmentTypeIcon(assessment.assessment_type)}</span>
          <h4>{assessment.assessment_type}</h4>
        </div>
        <div className="assessment-meta">
          <span className="assessment-date">{formatAssessmentDate(assessment.date)}</span>
          {assessment.assessor && (
            <span className="assessment-assessor">by {assessment.assessor}</span>
          )}
        </div>
      </div>

      <div className="assessment-content">
        <AssessmentResults results={assessment.results} />

        {assessment.recommendations && (
          <div className="assessment-recommendations">
            <h5>Recommendations & Behavior Plan</h5>
            <div className="recommendations-content">
              {assessment.recommendations}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

BehavioralAssessmentCard.propTypes = {
  assessment: PropTypes.shape({
    assessment_type: PropTypes.string,
    date: PropTypes.string,
    assessor: PropTypes.string,
    results: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
    recommendations: PropTypes.string
  }).isRequired
};

function StaffOnlyMessage() {
  return (
    <div className="staff-only-message">
      <div className="staff-only-icon">🔒</div>
      <h3>Staff Only Access</h3>
      <p>Behavioral assessment details are restricted to Muttville staff and volunteers with appropriate permissions.</p>
      <p>This helps ensure privacy and allows for proper handling of sensitive behavioral information.</p>
    </div>
  );
}

export function BehavioralAssessmentsSection({ behavioralAssessments }) {
  const { hasRole } = useAuth();
  const hasStaffAccess = hasRole('staff');

  if (!behavioralAssessments || behavioralAssessments.length === 0) {
    if (!hasStaffAccess) {
      return null; // Don't show section at all if no data and no access
    }

    return (
      <section className="behavioral-assessments-section">
        <h2 className="section-title">🧠 Behavioral Assessments</h2>
        <div className="no-data-message">
          <p>No behavioral assessments available for this dog.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="behavioral-assessments-section">
      <h2 className="section-title">🧠 Behavioral Assessments</h2>

      {!hasStaffAccess ? (
        <StaffOnlyMessage />
      ) : (
        <div className="behavioral-assessments-content">
          <div className="assessments-intro">
            <p>Behavioral assessments help us understand each dog&apos;s personality, needs, and compatibility. These evaluations guide training plans and adoption recommendations.</p>
          </div>

          <div className="behavioral-assessments-list">
            {behavioralAssessments.map((assessment, index) => (
              <BehavioralAssessmentCard
                key={`${assessment.assessment_type}-${assessment.date}-${index}`}
                assessment={assessment}
              />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

BehavioralAssessmentsSection.propTypes = {
  behavioralAssessments: PropTypes.arrayOf(
    PropTypes.shape({
      assessment_type: PropTypes.string,
      date: PropTypes.string,
      assessor: PropTypes.string,
      results: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
      recommendations: PropTypes.string
    })
  )
};
