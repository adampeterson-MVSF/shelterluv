import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import './PhotoGallery.css';

function usePhotoModalKeyboard(onClose, onNext, onPrevious) {
  useEffect(() => {
    const handleKeyDown = (event) => {
      switch (event.key) {
        case 'Escape':
          onClose();
          break;
        case 'ArrowLeft':
          onPrevious();
          break;
        case 'ArrowRight':
          onNext();
          break;
        default:
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [onClose, onNext, onPrevious]);
}

function PhotoModal({ photos, currentIndex, dogName, onClose, onNext, onPrevious }) {
  usePhotoModalKeyboard(onClose, onNext, onPrevious);

  if (!photos || photos.length === 0 || currentIndex < 0 || currentIndex >= photos.length) {
    return null;
  }

  const currentPhoto = photos[currentIndex];

  return (
    <div className="photo-modal-overlay" onClick={onClose}>
      <div className="photo-modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="photo-modal-close" onClick={onClose} aria-label="Close">
          ×
        </button>
        {photos.length > 1 && (
          <>
            <button
              className="photo-modal-nav photo-modal-prev"
              onClick={onPrevious}
              aria-label="Previous photo"
              disabled={currentIndex === 0}
            >
              ‹
            </button>
            <button
              className="photo-modal-nav photo-modal-next"
              onClick={onNext}
              aria-label="Next photo"
              disabled={currentIndex === photos.length - 1}
            >
              ›
            </button>
          </>
        )}
        <img
          src={currentPhoto}
          alt={`${dogName} ${currentIndex + 1} of ${photos.length}`}
          className="photo-modal-image"
        />
        <div className="photo-modal-counter">
          {currentIndex + 1} / {photos.length}
        </div>
      </div>
    </div>
  );
}

PhotoModal.propTypes = {
  photos: PropTypes.array.isRequired,
  currentIndex: PropTypes.number.isRequired,
  dogName: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
  onNext: PropTypes.func.isRequired,
  onPrevious: PropTypes.func.isRequired
};

function createPhotoNavigation(setFullscreenIndex, total) {
  return {
    openFullscreen: (index) => setFullscreenIndex(index),
    closeFullscreen: () => setFullscreenIndex(null),
    nextPhoto: () => setFullscreenIndex((prev) => (prev < total - 1 ? prev + 1 : prev)),
    previousPhoto: () => setFullscreenIndex((prev) => (prev > 0 ? prev - 1 : prev))
  };
}

export default function PhotoGallery({ photos, dogName }) {
  const [fullscreenIndex, setFullscreenIndex] = useState(null);

  if (!photos || photos.length === 0) return null;

  const { openFullscreen, closeFullscreen, nextPhoto, previousPhoto } = createPhotoNavigation(
    setFullscreenIndex,
    photos.length
  );

  return (
    <>
      <div className="photo-gallery">
        {photos.map((photo, index) => (
          <img
            key={index}
            src={photo}
            alt={`${dogName} ${index + 1}`}
            className="dog-photo"
            onClick={() => openFullscreen(index)}
            style={{ cursor: 'pointer' }}
          />
        ))}
      </div>
      {fullscreenIndex !== null && (
        <PhotoModal
          photos={photos}
          currentIndex={fullscreenIndex}
          dogName={dogName}
          onClose={closeFullscreen}
          onNext={nextPhoto}
          onPrevious={previousPhoto}
        />
      )}
    </>
  );
}

PhotoGallery.propTypes = {
  photos: PropTypes.array,
  dogName: PropTypes.string.isRequired
};


