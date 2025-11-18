import { memo, useMemo, useState } from 'react';
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
    'Status Change': '🔄',
    'Transfer': '🚚',
    'Death': '💔',
    'Lost': '🔍',
    'Found': '🎉',
    'Surgery': '🔪',
    'Vaccination': '💉',
    'Treatment': '💊',
    'Assessment': '📋',
    'Training': '🎓',
    'Photo': '📸',
    'Weight Check': '⚖️',
    'Spay/Neuter': '✂️'
  };
  return iconMap[eventType] || '📅';
}

function getEventColor(eventType) {
  const colorMap = {
    'Intake': '#3498db',
    'Adoption': '#27ae60',
    'Adoption Return': '#e74c3c',
    'Pending Adoption': '#f39c12',
    'Available': '#2ecc71',
    'Foster': '#9b59b6',
    'Medical': '#e74c3c',
    'Behavior': '#f39c12',
    'Status Change': '#95a5a6',
    'Transfer': '#34495e',
    'Death': '#2c3e50',
    'Lost': '#e67e22',
    'Found': '#27ae60',
    'Surgery': '#c0392b',
    'Vaccination': '#16a085',
    'Treatment': '#8e44ad',
    'Assessment': '#f1c40f',
    'Training': '#3498db',
    'Photo': '#9b59b6',
    'Weight Check': '#e67e22',
    'Spay/Neuter': '#e74c3c'
  };
  return colorMap[eventType] || '#3498db';
}

const EventTimelineItem = memo(function EventTimelineItem({ event, isLast }) {
  const eventColor = getEventColor(event.event_type);
  const icon = getEventIcon(event.event_type);

  return (
    <div className="event-timeline-item">
      <div className="event-timeline-marker">
        <span
          className="event-icon"
          style={{ backgroundColor: eventColor }}
        >
          {icon}
        </span>
        {!isLast && <div className="event-timeline-line" style={{ backgroundColor: eventColor }}></div>}
      </div>
      <div className="event-timeline-content" style={{ borderLeftColor: eventColor }}>
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
});

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

export const EventHistorySection = memo(function EventHistorySection({ eventHistory }) {
  const [showAllEvents, setShowAllEvents] = useState(false);

  const sortedEvents = useMemo(() => {
    if (!eventHistory || eventHistory.length === 0) return [];
    return [...eventHistory].sort((a, b) => {
      if (!a.date && !b.date) return 0;
      if (!a.date) return 1;
      if (!b.date) return -1;
      return new Date(b.date) - new Date(a.date);
    });
  }, [eventHistory]);

  const displayedEvents = useMemo(() => {
    if (showAllEvents || sortedEvents.length <= 10) {
      return sortedEvents;
    }
    return sortedEvents.slice(0, 10);
  }, [sortedEvents, showAllEvents]);

  if (!sortedEvents || sortedEvents.length === 0) {
    return (
      <section className="event-history-section">
        <h2 className="section-title">📅 Event History</h2>
        <div className="no-data-message">
          <p>No event history available for this dog.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="event-history-section">
      <h2 className="section-title">📅 Event History</h2>
      <div className="event-timeline">
        {displayedEvents.map((event, index) => (
          <EventTimelineItem
            key={`${event.event_type}-${event.date}-${index}`}
            event={event}
            isLast={index === displayedEvents.length - 1 && (showAllEvents || sortedEvents.length <= 10)}
          />
        ))}
      </div>

      {sortedEvents.length > 10 && !showAllEvents && (
        <div className="event-show-more">
          <button
            type="button"
            onClick={() => setShowAllEvents(true)}
            className="show-more-button"
          >
            Show All {sortedEvents.length} Events
          </button>
        </div>
      )}
    </section>
  );
});

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
