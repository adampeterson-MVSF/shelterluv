/**
 * Tests for DogCard component
 */

import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { DogCard } from './DogCard.jsx';
import { renderWithRouter } from '../test/testUtils';

// Mock the required modules
vi.mock('../types/dogNormalize', () => ({
  getPrimaryPhoto: vi.fn()
}));

vi.mock('../statusMapping.js', () => ({
  getStatusDisplay: vi.fn()
}));

const mockDog = {
  id: '123',
  Name: 'Buddy',
  Breed: 'Golden Retriever',
  AgeDisplay: '3 years',
  Size: 'Large',
  Gender: 'Male',
  Weight: '75',
  Status: 'AVAILABLE'
};


describe('DogCard', () => {
  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();
  });

  it('should render dog card with all information', async () => {
    const { getPrimaryPhoto } = await import('../types/dogNormalize');
    const { getStatusDisplay } = await import('../statusMapping.js');

    getPrimaryPhoto.mockReturnValue('/test-photo.jpg');
    getStatusDisplay.mockReturnValue({
      text: 'Available',
      className: 'available'
    });

    renderWithRouter(<DogCard dog={mockDog} />);

    // Check main elements
    expect(screen.getByText('Buddy')).toBeInTheDocument();
    expect(screen.getByText('Golden Retriever')).toBeInTheDocument();
    expect(screen.getByText('3 years')).toBeInTheDocument();
    expect(screen.getByText('Large')).toBeInTheDocument();
    expect(screen.getByText('Male')).toBeInTheDocument();
    expect(screen.getByText('75 lbs')).toBeInTheDocument();

    // Check image and status badge
    const image = screen.getByAltText('Buddy');
    expect(image).toHaveAttribute('src', '/test-photo.jpg');
    expect(screen.getByText('Available')).toHaveClass('available');
  });

  it('should render with placeholder image when no photo available', async () => {
    const { getPrimaryPhoto } = await import('../types/dogNormalize');
    const { getStatusDisplay } = await import('../statusMapping.js');

    getPrimaryPhoto.mockReturnValue(null);
    getStatusDisplay.mockReturnValue({
      text: 'Pending',
      className: 'pending'
    });

    renderWithRouter(<DogCard dog={mockDog} />);

    const image = screen.getByAltText('Buddy');
    expect(image).toHaveAttribute('src', '/placeholder-dog.png');
  });

  it('should render AVAILABLE status correctly', async () => {
    const { getPrimaryPhoto } = await import('../types/dogNormalize');
    const { getStatusDisplay } = await import('../statusMapping.js');

    getPrimaryPhoto.mockReturnValue('/test-photo.jpg');
    getStatusDisplay.mockReturnValue({
      text: 'Available',
      className: 'status-available'
    });

    const availableDog = { ...mockDog, Status: 'AVAILABLE' };
    renderWithRouter(<DogCard dog={availableDog} />);

    expect(screen.getByText('Available')).toHaveClass('status-available');
  });

  it('should render ADOPTED status correctly', async () => {
    const { getPrimaryPhoto } = await import('../types/dogNormalize');
    const { getStatusDisplay } = await import('../statusMapping.js');

    getPrimaryPhoto.mockReturnValue('/test-photo.jpg');
    getStatusDisplay.mockReturnValue({
      text: 'Adopted',
      className: 'status-adopted'
    });

    const adoptedDog = { ...mockDog, Status: 'ADOPTED' };
    renderWithRouter(<DogCard dog={adoptedDog} />);

    expect(screen.getByText('Adopted')).toHaveClass('status-adopted');
  });

  it('should render PENDING status correctly', async () => {
    const { getPrimaryPhoto } = await import('../types/dogNormalize');
    const { getStatusDisplay } = await import('../statusMapping.js');

    getPrimaryPhoto.mockReturnValue('/test-photo.jpg');
    getStatusDisplay.mockReturnValue({
      text: 'Pending',
      className: 'status-pending'
    });

    const pendingDog = { ...mockDog, Status: 'PENDING' };
    renderWithRouter(<DogCard dog={pendingDog} />);

    expect(screen.getByText('Pending')).toHaveClass('status-pending');
  });

  it('should render HOLD status correctly', async () => {
    const { getPrimaryPhoto } = await import('../types/dogNormalize');
    const { getStatusDisplay } = await import('../statusMapping.js');

    getPrimaryPhoto.mockReturnValue('/test-photo.jpg');
    getStatusDisplay.mockReturnValue({
      text: 'Hold',
      className: 'status-hold'
    });

    const holdDog = { ...mockDog, Status: 'HOLD' };
    renderWithRouter(<DogCard dog={holdDog} />);

    expect(screen.getByText('Hold')).toHaveClass('status-hold');
  });

  it('should render UNKNOWN status correctly', async () => {
    const { getPrimaryPhoto } = await import('../types/dogNormalize');
    const { getStatusDisplay } = await import('../statusMapping.js');

    getPrimaryPhoto.mockReturnValue('/test-photo.jpg');
    getStatusDisplay.mockReturnValue({
      text: 'Unknown',
      className: 'status-unknown'
    });

    const unknownDog = { ...mockDog, Status: 'UNKNOWN' };
    renderWithRouter(<DogCard dog={unknownDog} />);

    expect(screen.getByText('Unknown')).toHaveClass('status-unknown');
  });
});