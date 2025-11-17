import PropTypes from 'prop-types';

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

export function DogMetaSection({ dog }) {
  const metaItems = [
    { label: 'Intake Date', value: dog.IntakeDate },
    { label: 'Location', value: dog.Location },
    { label: 'Stage', value: dog.Stage },
    { label: 'Adoption Category', value: dog.AdoptionCategory },
    { label: 'Medical Category', value: dog.MedicalCategory },
    { label: 'Behavior Category', value: dog.BehaviorCategory },
    { label: 'Volunteer Category', value: dog.VolunteerCategory }
  ].filter((item) => item.value);

  const flagItems = [
    { label: 'In Custody', value: dog.IsInCustody },
    { label: 'Available', value: dog.IsAvailableForAdoption },
    { label: 'Hospice', value: dog.IsHospice },
    { label: 'Event Dog', value: dog.IsEventDog }
  ];

  const fosterDetails = dog.FosterName || dog.FosterEmail || dog.FosterPhone;

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

      {fosterDetails && (
        <div className="attributes-section">
          <h3 className="attributes-section-title">Foster Contact</h3>
          <ul className="attributes-list">
            {dog.FosterName && <li>Foster – {dog.FosterName}</li>}
            {dog.FosterEmail && <li>Email – {dog.FosterEmail}</li>}
            {dog.FosterPhone && <li>Phone – {dog.FosterPhone}</li>}
          </ul>
        </div>
      )}

      <div className="attributes-badges-list" style={{ marginTop: '1rem', gap: '0.75rem' }}>
        {flagItems
          .filter((flag) => flag.value)
          .map((flag) => (
            <span key={flag.label} className="attribute-badge">
              {flag.label}
            </span>
          ))}
      </div>

      <DogTreatmentsTable treatments={dog.Treatments} />
    </section>
  );
}

DogMetaSection.propTypes = {
  dog: PropTypes.object.isRequired
};


