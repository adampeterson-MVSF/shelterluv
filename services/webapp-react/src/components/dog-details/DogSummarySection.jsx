import PropTypes from 'prop-types';
import PhotoGallery from './PhotoGallery';

function DogStatusBanner({ dog }) {
  return (
    <div className="dog-status-banner">
      <p className="dog-status-line">{dog.Status || 'Unknown'}</p>
      <p className="dog-status-sub">
        Currently at <span className="strong">{dog.Location || 'Unknown'}</span>
      </p>
      <p className="dog-status-sub">
        Case Manager: <span className="strong">{dog.CaseManager || 'Not Assigned'}</span>
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
      <PhotoGallery photos={dog.Photos} dogName={dog.Name} />
    </section>
  );
}

DogSummarySection.propTypes = {
  dog: PropTypes.object.isRequired
};


