import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { getPrimaryPhoto } from '../types/dogNormalize';
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

  const photoUrl = getPrimaryPhoto(dog) || '/placeholder-dog.png';
  const statusDisplay = getStatusDisplay(dog.Status);

  return (
    <Link to={`/dog/${dog.id}`} className="dog-card">
      <div className="dog-card-inner">
        <div className="dog-card-image">
          <img src={photoUrl} alt={dog.Name} loading="lazy" />
        </div>
        <div className="dog-card-content">
          <h3 className="dog-card-name">{dog.Name}</h3>
          <p className="dog-card-breed">{dog.Breed}</p>
          <div className="dog-card-tags">
            {dog.AgeDisplay && <span className="dog-tag">{dog.AgeDisplay}</span>}
            {dog.Size && <span className="dog-tag">{dog.Size}</span>}
            {dog.Gender && <span className="dog-tag">{dog.Gender}</span>}
            {dog.Weight && <span className="dog-tag">{dog.Weight} lbs</span>}
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
    Name: PropTypes.string,
    Breed: PropTypes.string,
    AgeDisplay: PropTypes.string,
    Size: PropTypes.string,
    Gender: PropTypes.string,
    Weight: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    Status: PropTypes.string
  }).isRequired
};
