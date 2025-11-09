import { useParams, Link } from 'react-router-dom';
import PropTypes from 'prop-types';
import { useDogDetails } from '../hooks/useDogDetails';
import { daysAtMuttville, getShelterLuvUrl } from '../types/dogDerived';

function LoadingState() {
  return (
    <div className="page-container">
      <div className="loading">Loading dog details...</div>
    </div>
  );
}

function ErrorState({ error }) {
  return (
    <div className="page-container dog-details-page">
      <Link to="/" className="back-link">← Back to all dogs</Link>
      <div className="error-state">
        <h2>Unable to load dog</h2>
        <p>{error}</p>
        <Link to="/" className="btn-primary">View all dogs</Link>
      </div>
    </div>
  );
}

ErrorState.propTypes = {
  error: PropTypes.string.isRequired
};

function NotFoundState() {
  return (
    <div className="page-container dog-details-page">
      <Link to="/" className="back-link">← Back to all dogs</Link>
      <div className="error-state">
        <h2>Dog not found</h2>
        <p>This dog may have been adopted or the information is no longer available.</p>
        <Link to="/" className="btn-primary">View all dogs</Link>
      </div>
    </div>
  );
}

function DogInfo({ dog }) {
  return (
    <div className="dog-info">
      {dog.Breed && <p><strong>Breed:</strong> {dog.Breed}</p>}
      {dog.AgeDisplay && <p><strong>Age:</strong> {dog.AgeDisplay}</p>}
      {dog.Size && <p><strong>Size:</strong> {dog.Size}</p>}
      {daysAtMuttville(dog) > 0 && <p><strong>Time at Muttville:</strong> {daysAtMuttville(dog)} days</p>}
    </div>
  );
}

DogInfo.propTypes = {
  dog: PropTypes.object.isRequired
};

function PhotoGallery({ photos, dogName }) {
  if (!photos || photos.length === 0) return null;

  return (
    <div className="photo-gallery">
      {photos.slice(0, 3).map((photo, index) => (
        <img
          key={index}
          src={photo}
          alt={`${dogName} ${index + 1}`}
          className="dog-photo"
        />
      ))}
    </div>
  );
}

PhotoGallery.propTypes = {
  photos: PropTypes.array,
  dogName: PropTypes.string.isRequired
};

function DogContent({ dog }) {
  return (
    <div className="page-container dog-details-page">
      <Link to="/" className="back-link">← Back to all dogs</Link>
      <div className="dog-header">
        <h1>{dog.Name}</h1>
        <span className={`status-badge status-${dog.Status?.toLowerCase()}`}>
          {dog.Status || dog.Stage}
        </span>
        <DogInfo dog={dog} />
        <PhotoGallery photos={dog.Photos} dogName={dog.Name} />
        <div className="external-link">
          <a
            href={getShelterLuvUrl(dog)}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary"
          >
            Open in ShelterLuv →
          </a>
        </div>
      </div>
    </div>
  );
}

DogContent.propTypes = {
  dog: PropTypes.object.isRequired
};

/**
 * Dog details page component - displays basic information for a specific dog
 * Simple display, no complex tabs or conditional logic per constraints
 * @returns {JSX.Element} DogDetails component
 */
function DogDetails() {
  const { id } = useParams();
  const { dog, loading, error } = useDogDetails(id);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;
  if (!dog) return <NotFoundState />;

  return <DogContent dog={dog} />;
}

export default DogDetails;
