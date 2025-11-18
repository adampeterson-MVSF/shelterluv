import PropTypes from 'prop-types';
import './CategoryHistorySection.css';

function formatCategoryDate(dateString) {
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

function getCategoryIcon(category) {
  const iconMap = {
    'Adoption': '🏡',
    'Medical': '🏥',
    'Behavior': '🧠',
    'Foster': '🏠',
    'Training': '🎓'
  };
  return iconMap[category] || '📋';
}

function CategoryChangeItem({ change, isLast }) {
  const isPositiveChange = change.details?.toLowerCase().includes('improved') ||
                          change.details?.toLowerCase().includes('completed') ||
                          change.details?.toLowerCase().includes('successful');

  return (
    <div className="category-change-item">
      <div className="category-change-marker">
        <span className="category-icon">{getCategoryIcon(change.category)}</span>
        {!isLast && <div className="category-change-line"></div>}
      </div>
      <div className="category-change-content">
        <div className="category-change-header">
          <h4 className="category-change-title">
            {change.category} Category Change
          </h4>
          <span className="category-change-date">{formatCategoryDate(change.date)}</span>
        </div>

        <div className="category-change-details">
          {change.old_value && change.new_value && (
            <div className="category-transition">
              <span className="category-old">{change.old_value}</span>
              <span className="category-arrow">→</span>
              <span className="category-new">{change.new_value}</span>
            </div>
          )}

          {change.assigned_by && (
            <div className="category-assigned-by">
              <strong>Changed by:</strong> {change.assigned_by}
            </div>
          )}

          {change.details && (
            <div className={`category-details ${isPositiveChange ? 'positive' : ''}`}>
              <strong>Details:</strong> {change.details}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

CategoryChangeItem.propTypes = {
  change: PropTypes.shape({
    category: PropTypes.string,
    date: PropTypes.string,
    old_value: PropTypes.string,
    new_value: PropTypes.string,
    assigned_by: PropTypes.string,
    details: PropTypes.string
  }).isRequired,
  isLast: PropTypes.bool.isRequired
};

function CategorySummary({ categoryHistory }) {
  // Group by category type and get current/latest values
  const categorySummary = categoryHistory.reduce((acc, change) => {
    if (!acc[change.category]) {
      acc[change.category] = {
        current: change.new_value || change.old_value,
        changes: 0,
        lastChange: change.date
      };
    }
    acc[change.category].changes += 1;
    if (new Date(change.date) > new Date(acc[change.category].lastChange)) {
      acc[change.category].current = change.new_value || change.old_value;
      acc[change.category].lastChange = change.date;
    }
    return acc;
  }, {});

  return (
    <div className="category-summary">
      <h4>Current Categories</h4>
      <div className="category-summary-grid">
        {Object.entries(categorySummary).map(([category, info]) => (
          <div key={category} className="category-summary-item">
            <div className="category-summary-header">
              <span className="category-icon">{getCategoryIcon(category)}</span>
              <span className="category-name">{category}</span>
            </div>
            <div className="category-summary-details">
              <div className="category-current-value">{info.current}</div>
              <div className="category-change-count">
                {info.changes} change{info.changes !== 1 ? 's' : ''}
              </div>
              <div className="category-last-change">
                Last: {formatCategoryDate(info.lastChange)}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

CategorySummary.propTypes = {
  categoryHistory: PropTypes.array.isRequired
};

export function CategoryHistorySection({ categoryHistory }) {
  if (!categoryHistory || categoryHistory.length === 0) {
    return (
      <section className="category-history-section">
        <h2 className="section-title">🏷️ Category History</h2>
        <div className="no-data-message">
          <p>No category history available for this dog.</p>
        </div>
      </section>
    );
  }

  // Sort by date (most recent first)
  const sortedHistory = [...categoryHistory].sort((a, b) => {
    if (!a.date && !b.date) return 0;
    if (!a.date) return 1;
    if (!b.date) return -1;
    return new Date(b.date) - new Date(a.date);
  });

  return (
    <section className="category-history-section">
      <h2 className="section-title">🏷️ Category History</h2>

      <CategorySummary categoryHistory={categoryHistory} />

      <div className="category-changes-timeline">
        <h3>Change Timeline</h3>
        <div className="category-timeline">
          {sortedHistory.map((change, index) => (
            <CategoryChangeItem
              key={`${change.category}-${change.date}-${index}`}
              change={change}
              isLast={index === sortedHistory.length - 1}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

CategoryHistorySection.propTypes = {
  categoryHistory: PropTypes.arrayOf(
    PropTypes.shape({
      category: PropTypes.string,
      date: PropTypes.string,
      old_value: PropTypes.string,
      new_value: PropTypes.string,
      assigned_by: PropTypes.string,
      details: PropTypes.string
    })
  )
};
