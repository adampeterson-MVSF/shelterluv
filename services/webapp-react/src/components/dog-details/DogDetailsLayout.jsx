import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { DogSummarySection } from './DogSummarySection';
import { DogMetricsSection } from './DogMetricsSection';
import { DogNotesSection } from './DogNotesSection';
import { DogMetaSection } from './DogMetaSection';

function DogDetailsHeader({ dog }) {
  return (
    <header className="dog-detail-header">
      <div className="dog-detail-header-inner">
        <Link to="/" className="dog-detail-back">
          ←
        </Link>
        <h1 className="dog-detail-title">
          Muttville <span className="highlight">{dog.Name}</span>
        </h1>
      </div>
    </header>
  );
}

DogDetailsHeader.propTypes = {
  dog: PropTypes.object.isRequired
};

export function DogDetailsLayout({ dog }) {
  return (
    <>
      <DogDetailsHeader dog={dog} />
      <div className="page-container dog-details-page">
        <DogSummarySection dog={dog} />
        <DogMetricsSection dog={dog} />
        <DogNotesSection dog={dog} />
        <DogMetaSection dog={dog} />
      </div>
    </>
  );
}

DogDetailsLayout.propTypes = {
  dog: PropTypes.object.isRequired
};

