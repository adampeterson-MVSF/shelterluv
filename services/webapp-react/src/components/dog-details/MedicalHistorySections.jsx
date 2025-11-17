import PropTypes from 'prop-types';

function renderVaccination(vaccine) {
  return (
    <div className="medical-item">
      <div className="item-header">
        <strong>{vaccine.name}</strong>
        {vaccine.status && <span className="status-badge">{vaccine.status}</span>}
      </div>
      <div className="item-details">
        {vaccine.date && (
          <span>
            <strong>Date:</strong> {vaccine.date}
          </span>
        )}
        {vaccine.expiration_date && (
          <span>
            <strong>Expires:</strong> {vaccine.expiration_date}
          </span>
        )}
        {vaccine.lot_number && (
          <span>
            <strong>Lot:</strong> {vaccine.lot_number}
          </span>
        )}
        {vaccine.rabies_tag_number && (
          <span>
            <strong>Tag:</strong> {vaccine.rabies_tag_number}
          </span>
        )}
      </div>
    </div>
  );
}

function renderTreatment(treatment) {
  return (
    <div className="medical-item">
      <div className="item-header">
        <strong>{treatment.name}</strong>
      </div>
      <div className="item-details">
        {treatment.dosage && (
          <span>
            <strong>Dosage:</strong> {treatment.dosage}
          </span>
        )}
        {treatment.frequency && (
          <span>
            <strong>Frequency:</strong> {treatment.frequency}
          </span>
        )}
        {treatment.due_date && (
          <span>
            <strong>Due:</strong> {treatment.due_date}
          </span>
        )}
      </div>
    </div>
  );
}

function renderTreatmentHistory(treatment) {
  return (
    <div className="medical-item">
      <div className="item-header">
        <strong>{treatment.name}</strong>
      </div>
      <div className="item-details">
        {treatment.dosage && (
          <span>
            <strong>Dosage:</strong> {treatment.dosage}
          </span>
        )}
        {treatment.frequency && (
          <span>
            <strong>Frequency:</strong> {treatment.frequency}
          </span>
        )}
        {treatment.start_date && (
          <span>
            <strong>Start:</strong> {treatment.start_date}
          </span>
        )}
        {treatment.end_date && (
          <span>
            <strong>End:</strong> {treatment.end_date}
          </span>
        )}
        {treatment.notes && (
          <div className="treatment-notes">
            <strong>Notes:</strong> {treatment.notes}
          </div>
        )}
      </div>
    </div>
  );
}

function renderDiagnosis(diagnosis, variant) {
  return (
    <div className="medical-item">
      <div className="item-header">
        <strong>{diagnosis.condition}</strong>
        <span className={`status-badge ${variant}`}>{variant === 'resolved' ? 'Resolved' : 'Active'}</span>
      </div>
      <div className="item-details">
        {diagnosis.diagnosed_date && (
          <span>
            <strong>Diagnosed:</strong> {diagnosis.diagnosed_date}
          </span>
        )}
        {diagnosis.resolved_date && (
          <span>
            <strong>Resolved:</strong> {diagnosis.resolved_date}
          </span>
        )}
        {diagnosis.notes && (
          <div className="diagnosis-notes">
            <strong>Notes:</strong> {diagnosis.notes}
          </div>
        )}
      </div>
    </div>
  );
}

function renderTest(test) {
  return (
    <div className="medical-item">
      <div className="item-header">
        <strong>{test.test_name}</strong>
        {test.test_type && <span className="test-type">{test.test_type}</span>}
      </div>
      <div className="item-details">
        {test.date && (
          <span>
            <strong>Date:</strong> {test.date}
          </span>
        )}
        {test.results && (
          <div className="test-results">
            <strong>Results:</strong> {test.results}
          </div>
        )}
        {test.notes && (
          <div className="test-notes">
            <strong>Notes:</strong> {test.notes}
          </div>
        )}
      </div>
    </div>
  );
}

function renderExam(exam) {
  return (
    <div className="medical-item">
      <div className="item-header">
        <strong>{exam.exam_type}</strong>
      </div>
      <div className="item-details">
        {exam.date_time && (
          <span>
            <strong>Date:</strong> {exam.date_time}
          </span>
        )}
        {exam.details && (
          <div className="exam-details">
            <strong>Details:</strong> {exam.details}
          </div>
        )}
      </div>
    </div>
  );
}

function renderProcedure(procedure) {
  return (
    <div className="medical-item">
      <div className="item-header">
        <strong>{procedure.procedure_type}</strong>
      </div>
      <div className="item-details">
        {procedure.date_time && (
          <span>
            <strong>Date:</strong> {procedure.date_time}
          </span>
        )}
        {procedure.details && (
          <div className="procedure-details">
            <strong>Details:</strong> {procedure.details}
          </div>
        )}
      </div>
    </div>
  );
}

function MedicalHistorySection({ title, items, renderItem }) {
  if (!items || items.length === 0) return null;

  return (
    <div className="medical-section">
      <h3 className="section-title">{title}</h3>
      <div className="section-content">
        {items.map((item, index) => (
          <div key={`${title}-${index}`}>{renderItem(item)}</div>
        ))}
      </div>
    </div>
  );
}

MedicalHistorySection.propTypes = {
  title: PropTypes.string.isRequired,
  items: PropTypes.array.isRequired,
  renderItem: PropTypes.func.isRequired
};

export function MedicalHistorySections({ medicalHistory }) {
  if (!medicalHistory) return null;

  return (
    <>
      <MedicalHistorySection
        title="💉 Vaccination History"
        items={medicalHistory.vaccinations}
        renderItem={renderVaccination}
      />
      <MedicalHistorySection
        title="⏰ Treatments Next Due"
        items={medicalHistory.treatments_due}
        renderItem={renderTreatment}
      />
      <MedicalHistorySection
        title="📋 Treatment History"
        items={medicalHistory.treatment_history}
        renderItem={renderTreatmentHistory}
      />
      <MedicalHistorySection
        title="🔴 Active Diagnoses"
        items={medicalHistory.active_diagnoses}
        renderItem={(item) => renderDiagnosis(item, 'active')}
      />
      <MedicalHistorySection
        title="✅ Resolved Diagnoses"
        items={medicalHistory.resolved_diagnoses}
        renderItem={(item) => renderDiagnosis(item, 'resolved')}
      />
      <MedicalHistorySection
        title="🧪 Diagnostic Tests"
        items={medicalHistory.diagnostic_tests}
        renderItem={renderTest}
      />
      <MedicalHistorySection
        title="👨‍⚕️ Physical Exams"
        items={medicalHistory.physical_exams}
        renderItem={renderExam}
      />
      <MedicalHistorySection
        title="🏥 Procedures & Surgeries"
        items={medicalHistory.procedures_surgeries}
        renderItem={renderProcedure}
      />
    </>
  );
}

MedicalHistorySections.propTypes = {
  medicalHistory: PropTypes.object
};


