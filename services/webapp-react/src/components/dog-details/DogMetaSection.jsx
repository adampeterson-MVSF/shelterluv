import PropTypes from 'prop-types';
import { useAuth } from '../../contexts/AuthContext';

function DogTreatmentsTable({ treatments }) {
  if (!treatments || treatments.length === 0) return null;

  return (
    <section className="dog-treatments-section">
      <h2 className="dog-treatments-title">Treatments</h2>
      <div className="dog-treatments-table">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Treatment</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {treatments.map((treatment, index) => (
              <tr key={index}>
                <td>{treatment.date || '—'}</td>
                <td>{treatment.treatment || '—'}</td>
                <td>{treatment.notes || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

DogTreatmentsTable.propTypes = {
  treatments: PropTypes.array
};

function prepareMetaItems(dog) {
  return [
    { label: 'Intake Date', value: dog.lastIntakeAt ? new Date(dog.lastIntakeAt).toLocaleDateString() : null },
    { label: 'Location', value: dog.location?.label },
    { label: 'Adoption Fee Group', value: dog.admin?.adoptionFeeGroup },
    { label: 'Litter Group', value: dog.admin?.litterGroupId }
  ].filter((item) => item.value);
}

function prepareFlagItems(dog) {
  return [
    { label: 'In Foster', value: dog.inFoster },
    { label: 'Available', value: dog.status === 'available' },
    { label: 'Altered', value: dog.physical?.altered }
  ].filter(flag => flag.value !== null && flag.value !== undefined);
}

function renderFosterSection(dog, isStaff) {
  const fosterPerson = dog.foster?.person;
  const hasFosterDetails = fosterPerson && (fosterPerson.firstName || fosterPerson.email || fosterPerson.phone);

  if (!hasFosterDetails || !isStaff) {
    return null;
  }

  return (
    <div className="attributes-section">
      <h3 className="attributes-section-title">Foster Contact</h3>
      <ul className="attributes-list">
        {(fosterPerson.firstName || fosterPerson.lastName) && (
          <li>Foster – {[fosterPerson.firstName, fosterPerson.lastName].filter(Boolean).join(' ')}</li>
        )}
        {fosterPerson.email && <li>Email – {fosterPerson.email}</li>}
        {fosterPerson.phone && <li>Phone – {fosterPerson.phone}</li>}
      </ul>
    </div>
  );
}

export function DogMetaSection({ dog }) {
  const { hasRole } = useAuth();
  const isStaff = hasRole('staff');

  const metaItems = prepareMetaItems(dog);
  const flagItems = prepareFlagItems(dog);

  return (
    <section className="dog-meta-section">
      <h2 className="dog-notes-title">Details</h2>
      {metaItems.length > 0 && (
        <ul className="attributes-list">
          {metaItems.map((item) => (
            <li key={item.label}>
              <strong>{item.label}:</strong> {item.value}
            </li>
          ))}
        </ul>
      )}

      {renderFosterSection(dog, isStaff)}

      <div className="attributes-badges-list" style={{ marginTop: '1rem', gap: '0.75rem' }}>
        {flagItems
          .filter((flag) => flag.value)
          .map((flag) => (
            <span key={flag.label} className="attribute-badge">
              {flag.label}
            </span>
          ))}
      </div>

      {/* TODO: Add treatments table when medical data is structured */}
    </section>
  );
}

DogMetaSection.propTypes = {
  dog: PropTypes.object.isRequired
};


