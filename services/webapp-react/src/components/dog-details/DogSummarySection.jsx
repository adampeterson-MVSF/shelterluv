import PropTypes from 'prop-types';
import PhotoGallery from './PhotoGallery';

function DogStatusBanner({ dog }) {
  const locationDisplay = dog.location?.label || 'Unknown';
  const caseManager = dog.admin?.adoptionFeeGroup || 'Not Assigned'; // Using adoptionFeeGroup as proxy for case manager

  return (
    <div className="dog-status-banner">
      <p className="dog-status-line">{dog.status || 'Unknown'}</p>
      <p className="dog-status-sub">
        Currently at <span className="strong">{locationDisplay}</span>
      </p>
      <p className="dog-status-sub">
        Case Manager: <span className="strong">{caseManager}</span>
      </p>
    </div>
  );
}

DogStatusBanner.propTypes = {
  dog: PropTypes.object.isRequired
};

export function DogSummarySection({ dog }) {
  return (
    <section className="dog-summary-section">
      <DogStatusBanner dog={dog} />
      <PhotoGallery photos={dog.media?.photos || []} dogName={dog.name} />
    </section>
  );
}

DogSummarySection.propTypes = {
  dog: PropTypes.object.isRequired
};


