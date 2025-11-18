import PropTypes from 'prop-types';
import './EventHistorySection.css';

function formatEventDate(dateString) {
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

function getEventIcon(eventType) {
  const iconMap = {
    'Intake': '📥',
    'Adoption': '🏡',
    'Adoption Return': '↩️',
    'Pending Adoption': '⏳',
    'Available': '✅',
    'Foster': '🏠',
    'Medical': '🏥',
    'Behavior': '🧠',
    'Status Change': '🔄'
  };
  return iconMap[eventType] || '📅';
}

function EventTimelineItem({ event, isLast }) {
  return (
    <div className="event-timeline-item">
      <div className="event-timeline-marker">
        <span className="event-icon">{getEventIcon(event.event_type)}</span>
        {!isLast && <div className="event-timeline-line"></div>}
      </div>
      <div className="event-timeline-content">
        <div className="event-header">
          <h4 className="event-title">{event.event_type}</h4>
          <span className="event-date">{formatEventDate(event.date)}</span>
        </div>
        {event.associated_person && (
          <div className="event-person">
            <strong>Associated:</strong> {event.associated_person}
          </div>
        )}
        {event.details && (
          <div className="event-details">{event.details}</div>
        )}
        {event.status_change && (
          <div className="event-status-change">
            <strong>Status:</strong> {event.status_change}
          </div>
        )}
      </div>
    </div>
  );
}

EventTimelineItem.propTypes = {
  event: PropTypes.shape({
    event_type: PropTypes.string,
    date: PropTypes.string,
    associated_person: PropTypes.string,
    details: PropTypes.string,
    status_change: PropTypes.string
  }).isRequired,
  isLast: PropTypes.bool.isRequired
};

export function EventHistorySection({ eventHistory }) {
  if (!eventHistory || eventHistory.length === 0) {
    return (
      <section className="event-history-section">
        <h2 className="section-title">📅 Event History</h2>
        <div className="no-data-message">
          <p>No event history available for this dog.</p>
        </div>
      </section>
    );
  }

  // Sort events by date (most recent first)
  const sortedEvents = [...eventHistory].sort((a, b) => {
    if (!a.date && !b.date) return 0;
    if (!a.date) return 1;
    if (!b.date) return -1;
    return new Date(b.date) - new Date(a.date);
  });

  return (
    <section className="event-history-section">
      <h2 className="section-title">📅 Event History</h2>
      <div className="event-timeline">
        {sortedEvents.map((event, index) => (
          <EventTimelineItem
            key={`${event.event_type}-${event.date}-${index}`}
            event={event}
            isLast={index === sortedEvents.length - 1}
          />
        ))}
      </div>
    </section>
  );
}

EventHistorySection.propTypes = {
  eventHistory: PropTypes.arrayOf(
    PropTypes.shape({
      event_type: PropTypes.string,
      date: PropTypes.string,
      associated_person: PropTypes.string,
      details: PropTypes.string,
      status_change: PropTypes.string
    })
  )
};
