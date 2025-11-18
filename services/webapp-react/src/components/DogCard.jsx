import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { getPrimaryPhoto, getAgeDisplay } from '../types/dogNormalize';
import { getStatusDisplay } from '../statusMapping.js';

/**
 * DogCard component - displays a dog in list view with basic information.
 * Simple display without conditional role-based rendering.
 *
 * @param {Object} props
 * @param {Dog} props.dog - Dog object to display
 */
export function DogCard({ dog }) {
  // Guarantee canonical ID field (Firestore document ID)
  const canonicalId = dog.id;
  if (!canonicalId) {
    console.error('DogCard: Missing canonical ID field', dog);
    return null; // Don't render card without ID
  }

  const photoUrl = dog.primaryPhotoUrl || getPrimaryPhoto(dog) || '/placeholder-dog.png';
  const statusDisplay = dog.statusDisplay || getStatusDisplay(dog.status);
  const ageDisplay = dog.ageDisplay || getAgeDisplay(dog.physical?.ageDays);

  return (
    <Link to={`/dog/${dog.id}`} className="dog-card">
      <div className="dog-card-inner">
        <div className="dog-card-image">
          <img src={photoUrl} alt={dog.name} loading="lazy" />
        </div>
        <div className="dog-card-content">
          <h3 className="dog-card-name">{dog.name}</h3>
          <p className="dog-card-breed">{dog.physical?.breed}</p>
          <div className="dog-card-tags">
            {ageDisplay && <span className="dog-tag">{ageDisplay}</span>}
            {dog.physical?.sizeLabel && <span className="dog-tag">{dog.physical.sizeLabel}</span>}
            {dog.physical?.sex && <span className="dog-tag">{dog.physical.sex}</span>}
            {dog.physical?.weightLbs && <span className="dog-tag">{dog.physical.weightLbs} lbs</span>}
            {dog.inFoster && <span className="dog-tag foster">In Foster</span>}
          </div>
          {statusDisplay?.text && (
            <div className="dog-card-status">
              <span
                className={`dog-card-status-badge ${statusDisplay.className || ''}`.trim()}
              >
                {statusDisplay.text}
              </span>
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}

DogCard.propTypes = {
  dog: PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string,
    physical: PropTypes.shape({
      breed: PropTypes.string,
      ageDays: PropTypes.number,
      sizeLabel: PropTypes.string,
      sex: PropTypes.string,
      weightLbs: PropTypes.number,
    }),
    inFoster: PropTypes.bool,
    status: PropTypes.string,
    primaryPhotoUrl: PropTypes.string,
    statusDisplay: PropTypes.shape({
      text: PropTypes.string,
      className: PropTypes.string
    }),
    ageDisplay: PropTypes.string,
  }).isRequired
};
