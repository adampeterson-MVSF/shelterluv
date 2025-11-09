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
  const photoUrl = getPrimaryPhoto(dog) || '/placeholder-dog.png';

  // Determine status badge color and text using centralized mapping
  const getStatusBadge = () => {
    return getStatusDisplay(dog.Status);
  };

  const statusBadge = getStatusBadge();

  return (
    <Link to={`/dog/${dog.id}`} className="dog-card">
      <div className="dog-card-image">
        <img src={photoUrl} alt={dog.Name} loading="lazy" />
        <span className={`status-badge ${statusBadge.className}`}>
          {statusBadge.text}
        </span>
      </div>

      <div className="dog-card-content">
        <h3 className="dog-card-name">{dog.Name}</h3>

        <div className="dog-card-details">
          {dog.Breed && <p className="dog-breed">{dog.Breed}</p>}

          <div className="dog-card-attributes">
            {dog.AgeDisplay && <span className="attribute">{dog.AgeDisplay}</span>}
            {dog.Size && <span className="attribute">{dog.Size}</span>}
            {dog.Gender && <span className="attribute">{dog.Gender}</span>}
            {dog.Weight && <span className="attribute">{dog.Weight} lbs</span>}
          </div>
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
    Status: PropTypes.string,
    Stage: PropTypes.string
  }).isRequired
};
