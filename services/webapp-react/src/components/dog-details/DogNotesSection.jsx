import { useState } from 'react';
import PropTypes from 'prop-types';
import { MedicalHistorySections } from './MedicalHistorySections';
import { EventHistorySection } from './EventHistorySection';
import { WeightHistorySection } from './WeightHistorySection';
import { CategoryHistorySection } from './CategoryHistorySection';
import { BehavioralAssessmentsSection } from './BehavioralAssessmentsSection';
import { CompatibilityWarningsSection } from './CompatibilityWarningsSection';
import { AttachedDocumentsSection } from './AttachedDocumentsSection';
import { useAuth } from '../../contexts/AuthContext';
import {
  shapeBasicAttributes,
  shapeMicrochipAttributes,
  shapeAlteredAttributes,
  shapeIntakeAttributes,
  shapeAdoptionAttributes,
  getBehavioralAttributes,
  getPhysicalAttributes,
  checkMedicalInfo
} from '../../types/dogDetailsHelpers';

function AttributeSection({ title, items, keyPrefix }) {
  if (!items.length) return null;

  return (
    <div className="attributes-section">
      <h3 className="attributes-section-title">{title}</h3>
      <ul className="attributes-list">
        {items.map((text, i) => (
          <li key={`${keyPrefix}-${i}`}>{text}</li>
        ))}
      </ul>
    </div>
  );
}

AttributeSection.propTypes = {
  title: PropTypes.string.isRequired,
  items: PropTypes.array.isRequired,
  keyPrefix: PropTypes.string.isRequired
};

function AttributesTab({ dog }) {
  const basicItems = shapeBasicAttributes(dog);
  const behavioralAttributes = getBehavioralAttributes(dog);
  const physicalAttributes = getPhysicalAttributes(dog);
  const microchipItems = shapeMicrochipAttributes(dog);
  const alteredItems = shapeAlteredAttributes(dog);
  const hasBadges = behavioralAttributes.length > 0 || physicalAttributes.length > 0;

  return (
    <>
      <ul className="attributes-list">
        {basicItems.map((text, index) => (
          <li key={index}>{text}</li>
        ))}
      </ul>

      <AttributeSection title="Microchip" items={microchipItems} keyPrefix="chip" />
      <AttributeSection title="Altered Status" items={alteredItems} keyPrefix="altered" />
      <AttributeSection title="Behavior Attributes" items={behavioralAttributes} keyPrefix="behav" />
      <AttributeSection title="Physical Attributes" items={physicalAttributes} keyPrefix="phys" />

      {/* Disclaimers Section */}
      {dog.Disclaimers && dog.Disclaimers.length > 0 && (
        <div className="attributes-section">
          <h3 className="attributes-section-title">Additional Information</h3>
          <ul className="attributes-list">
            {dog.Disclaimers.map((disclaimer, i) => (
              <li key={`disclaimer-${i}`}>
                <strong>{disclaimer.title}</strong>
                {disclaimer.content && (
                  <div style={{ marginTop: '4px', fontSize: '0.9em', color: '#666' }}>
                    {disclaimer.content}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {hasBadges && (
        <div className="attributes-badges">
          <h3 className="attributes-badges-title">All Attributes</h3>
          <div className="attributes-badges-list">
            {[...behavioralAttributes, ...physicalAttributes].map((attr, index) => (
              <span key={`badge-${index}`} className="attribute-badge">
                {attr}
              </span>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

AttributesTab.propTypes = {
  dog: PropTypes.object.isRequired
};

function IntakeTab({ dog }) {
  const { intakeItems, hasIntakeNotes } = shapeIntakeAttributes(dog);

  if (!intakeItems.length && !hasIntakeNotes) {
    return <p className="notes-paragraph">No intake information available.</p>;
  }

  return (
    <>
      {intakeItems.length > 0 && (
        <ul className="attributes-list">
          {intakeItems.map((text, index) => (
            <li key={index}>{text}</li>
          ))}
        </ul>
      )}
      {hasIntakeNotes && (
        <div className="attributes-section">
          <h3 className="attributes-section-title">Intake Notes</h3>
          <p className="notes-paragraph">{dog.IntakeNotes}</p>
        </div>
      )}
    </>
  );
}

IntakeTab.propTypes = {
  dog: PropTypes.object.isRequired
};

function AdoptionTab({ dog }) {
  const adoptionItems = shapeAdoptionAttributes(dog);

  if (!adoptionItems.length) {
    return <p className="notes-paragraph">No adoption information available.</p>;
  }

  return (
    <ul className="attributes-list">
      {adoptionItems.map((text, index) => (
        <li key={index}>{text}</li>
      ))}
    </ul>
  );
}

AdoptionTab.propTypes = {
  dog: PropTypes.object.isRequired
};

function PersonalityTab({ dog }) {
  const hasNotes = dog.PersonalityNotes && dog.PersonalityNotes !== 'Not Available';
  const hasWebsiteMemo = dog.WebsiteMemo && dog.WebsiteMemo.content;

  if (!hasNotes && !hasWebsiteMemo) {
    return <p className="notes-paragraph">No personality information available.</p>;
  }

  return (
    <div className="personality-notes">
      {hasWebsiteMemo && (
        <div className="website-memo-section">
          <h4 style={{ fontWeight: 'bold', marginBottom: '8px' }}>About {dog.Name}</h4>
          {dog.WebsiteMemo.author && dog.WebsiteMemo.date && (
            <div style={{ fontSize: '0.9em', color: '#666', marginBottom: '12px' }}>
              Written by {dog.WebsiteMemo.author} on {dog.WebsiteMemo.date}
            </div>
          )}
          <div style={{ lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
            {dog.WebsiteMemo.content}
          </div>
        </div>
      )}

      {hasNotes && (
        <div className="personality-notes-section" style={{ marginTop: hasWebsiteMemo ? '24px' : '0' }}>
          {hasWebsiteMemo && <h4 style={{ fontWeight: 'bold', marginBottom: '8px' }}>Additional Notes</h4>}
          <p className="notes-paragraph">{dog.PersonalityNotes}</p>
        </div>
      )}
    </div>
  );
}

PersonalityTab.propTypes = {
  dog: PropTypes.object.isRequired
};

function MedicalTab({ dog }) {
  const { hasMedicalHistory, hasMedicalNotes } = checkMedicalInfo(dog);
  const hasStructuredMedicalData = (
    (dog.MicrochipInfo && Object.keys(dog.MicrochipInfo).length > 0) ||
    (dog.RabiesTag && Object.keys(dog.RabiesTag).length > 0) ||
    (dog.VaccinationHistory && dog.VaccinationHistory.length > 0) ||
    (dog.TreatmentsDue && dog.TreatmentsDue.length > 0) ||
    (dog.TreatmentHistory && dog.TreatmentHistory.length > 0) ||
    (dog.Diagnoses && dog.Diagnoses.length > 0) ||
    (dog.DiagnosticTests && dog.DiagnosticTests.length > 0) ||
    (dog.PhysicalExams && dog.PhysicalExams.length > 0) ||
    (dog.Procedures && dog.Procedures.length > 0) ||
    (dog.MedicalMemos && dog.MedicalMemos.length > 0)
  );

  if (!hasMedicalHistory && !hasMedicalNotes && !hasStructuredMedicalData) {
    return <p className="notes-paragraph">No medical information available.</p>;
  }

  return (
    <div className="medical-notes">
      {/* Microchip Information */}
      {dog.MicrochipInfo && dog.MicrochipInfo.number && (
        <div className="medical-section">
          <h3 className="section-title">🆔 Microchip Information</h3>
          <div className="section-content">
            <ul className="attributes-list">
              <li><strong>Number:</strong> {dog.MicrochipInfo.number}</li>
              {dog.MicrochipInfo.issued_date && <li><strong>Issued:</strong> {dog.MicrochipInfo.issued_date}</li>}
              {dog.MicrochipInfo.issuer && <li><strong>Issuer:</strong> {dog.MicrochipInfo.issuer}</li>}
            </ul>
          </div>
        </div>
      )}

      {/* Rabies Tag */}
      {dog.RabiesTag && dog.RabiesTag.number && (
        <div className="medical-section">
          <h3 className="section-title">🏷️ Rabies Tag</h3>
          <div className="section-content">
            <p><strong>Number:</strong> {dog.RabiesTag.number}</p>
          </div>
        </div>
      )}

      {/* Vaccination History */}
      {dog.VaccinationHistory && dog.VaccinationHistory.length > 0 && (
        <div className="medical-section">
          <h3 className="section-title">💉 Vaccination History</h3>
          <div className="section-content">
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa' }}>
                    <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #dee2e6' }}>Vaccine</th>
                    <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #dee2e6' }}>Date</th>
                    <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #dee2e6' }}>Expires</th>
                    <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #dee2e6' }}>Route</th>
                    <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #dee2e6' }}>Site</th>
                  </tr>
                </thead>
                <tbody>
                  {dog.VaccinationHistory.map((vacc, i) => (
                    <tr key={i}>
                      <td style={{ padding: '8px', border: '1px solid #dee2e6' }}>{vacc.vaccine}</td>
                      <td style={{ padding: '8px', border: '1px solid #dee2e6' }}>{vacc.date}</td>
                      <td style={{ padding: '8px', border: '1px solid #dee2e6' }}>{vacc.expiration_date || 'N/A'}</td>
                      <td style={{ padding: '8px', border: '1px solid #dee2e6' }}>{vacc.route || 'N/A'}</td>
                      <td style={{ padding: '8px', border: '1px solid #dee2e6' }}>{vacc.site || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Treatments Due */}
      {dog.TreatmentsDue && dog.TreatmentsDue.length > 0 && (
        <div className="medical-section">
          <h3 className="section-title">⏰ Treatments Due</h3>
          <div className="section-content">
            <ul className="attributes-list">
              {dog.TreatmentsDue.map((treatment, i) => (
                <li key={i}>
                  <strong>{treatment.treatment}</strong>
                  <div style={{ fontSize: '0.9em', color: treatment.status === 'Overdue' ? '#dc3545' : '#666', marginTop: '4px' }}>
                    {treatment.dosage} • {treatment.frequency} • Due: {treatment.due_date} ({treatment.status})
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Treatment History */}
      {dog.TreatmentHistory && dog.TreatmentHistory.length > 0 && (
        <div className="medical-section">
          <h3 className="section-title">📋 Treatment History</h3>
          <div className="section-content">
            {dog.TreatmentHistory.map((treatment, i) => (
              <div key={i} style={{ marginBottom: '16px', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                <h4 style={{ margin: '0 0 8px 0', fontSize: '1.1em' }}>{treatment.treatment}</h4>
                <div style={{ fontSize: '0.9em', color: '#666' }}>
                  {treatment.dosage && <div><strong>Dosage:</strong> {treatment.dosage}</div>}
                  {treatment.frequency && <div><strong>Frequency:</strong> {treatment.frequency}</div>}
                  {(treatment.start_date || treatment.end_date) && (
                    <div><strong>Dates:</strong> {treatment.start_date || 'N/A'} to {treatment.end_date || 'Ongoing'}</div>
                  )}
                  {treatment.status && <div><strong>Status:</strong> {treatment.status}</div>}
                  {treatment.veterinarian && <div><strong>Veterinarian:</strong> {treatment.veterinarian}</div>}
                  {treatment.notes && <div style={{ marginTop: '8px' }}><strong>Notes:</strong> {treatment.notes}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Diagnoses */}
      {dog.Diagnoses && dog.Diagnoses.length > 0 && (
        <div className="medical-section">
          <h3 className="section-title">🔍 Diagnoses</h3>
          <div className="section-content">
            {dog.Diagnoses.map((diagnosis, i) => (
              <div key={i} style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                <h4 style={{ margin: '0 0 8px 0', color: diagnosis.status === 'Active' ? '#dc3545' : '#28a745' }}>
                  {diagnosis.condition} ({diagnosis.status})
                </h4>
                <div style={{ fontSize: '0.9em', color: '#666' }}>
                  <div><strong>Category:</strong> {diagnosis.category}</div>
                  {diagnosis.diagnosed_date && <div><strong>Diagnosed:</strong> {diagnosis.diagnosed_date}</div>}
                  {diagnosis.resolved_date && <div><strong>Resolved:</strong> {diagnosis.resolved_date}</div>}
                  {diagnosis.veterinarian && <div><strong>Veterinarian:</strong> {diagnosis.veterinarian}</div>}
                  {diagnosis.description && <div style={{ marginTop: '8px' }}><strong>Details:</strong> {diagnosis.description}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Diagnostic Tests */}
      {dog.DiagnosticTests && dog.DiagnosticTests.length > 0 && (
        <div className="medical-section">
          <h3 className="section-title">🧪 Diagnostic Tests</h3>
          <div className="section-content">
            {dog.DiagnosticTests.map((test, i) => (
              <div key={i} style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                <h4 style={{ margin: '0 0 8px 0' }}>{test.test_type} ({test.status})</h4>
                <div style={{ fontSize: '0.9em', color: '#666' }}>
                  <div><strong>Date:</strong> {test.date}</div>
                  {test.veterinarian && <div><strong>Veterinarian:</strong> {test.veterinarian}</div>}
                  {test.results && <div style={{ marginTop: '8px' }}><strong>Results:</strong> {test.results}</div>}
                  {test.notes && <div style={{ marginTop: '8px' }}><strong>Notes:</strong> {test.notes}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Physical Exams */}
      {dog.PhysicalExams && dog.PhysicalExams.length > 0 && (
        <div className="medical-section">
          <h3 className="section-title">👨‍⚕️ Physical Exams</h3>
          <div className="section-content">
            {dog.PhysicalExams.map((exam, i) => (
              <div key={i} style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                <h4 style={{ margin: '0 0 8px 0' }}>{exam.exam_type}</h4>
                <div style={{ fontSize: '0.9em', color: '#666' }}>
                  {exam.date && <div><strong>Date:</strong> {exam.date}</div>}
                  {exam.veterinarian && <div><strong>Veterinarian:</strong> {exam.veterinarian}</div>}
                  {exam.clinic && <div><strong>Clinic:</strong> {exam.clinic}</div>}
                  {exam.subjective && <div style={{ marginTop: '8px' }}><strong>Subjective:</strong> {exam.subjective}</div>}
                  {exam.objective && <div style={{ marginTop: '8px' }}><strong>Objective:</strong> {exam.objective}</div>}
                  {exam.assessment && <div style={{ marginTop: '8px' }}><strong>Assessment:</strong> {exam.assessment}</div>}
                  {exam.plan && <div style={{ marginTop: '8px' }}><strong>Plan:</strong> {exam.plan}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Procedures */}
      {dog.Procedures && dog.Procedures.length > 0 && (
        <div className="medical-section">
          <h3 className="section-title">🔧 Procedures</h3>
          <div className="section-content">
            {dog.Procedures.map((procedure, i) => (
              <div key={i} style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                <h4 style={{ margin: '0 0 8px 0' }}>{procedure.procedure} ({procedure.status})</h4>
                <div style={{ fontSize: '0.9em', color: '#666' }}>
                  <div><strong>Date:</strong> {procedure.date}</div>
                  {procedure.surgeon && <div><strong>Surgeon:</strong> {procedure.surgeon}</div>}
                  {procedure.clinic && <div><strong>Clinic:</strong> {procedure.clinic}</div>}
                  {procedure.notes && <div style={{ marginTop: '8px' }}><strong>Notes:</strong> {procedure.notes}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Medical Memos */}
      {dog.MedicalMemos && dog.MedicalMemos.length > 0 && (
        <div className="medical-section">
          <h3 className="section-title">📝 Medical Memos</h3>
          <div className="section-content">
            {dog.MedicalMemos.map((memo, i) => (
              <div key={i} style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                <div style={{ fontSize: '0.9em', color: '#666', marginBottom: '8px' }}>
                  {memo.date} by {memo.author}
                </div>
                <div style={{ whiteSpace: 'pre-wrap' }}>{memo.content}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Original Medical Notes */}
      {hasMedicalNotes && (
        <div className="medical-section">
          <h3 className="section-title">📝 Medical Notes</h3>
          <div className="section-content">
            <p className="notes-paragraph">{dog.MedicalNotes}</p>
          </div>
        </div>
      )}

      {/* Original Medical History */}
      <MedicalHistorySections medicalHistory={dog.MedicalHistory} />
    </div>
  );
}

MedicalTab.propTypes = {
  dog: PropTypes.object.isRequired
};

function HistoryTab({ dog }) {
  return (
    <div className="history-tab-content">
      <EventHistorySection eventHistory={dog.EventHistory} />
      <WeightHistorySection weightHistory={dog.WeightHistory} />
      <CategoryHistorySection categoryHistory={dog.CategoryHistory} />
    </div>
  );
}

HistoryTab.propTypes = {
  dog: PropTypes.object.isRequired
};

function BehaviorTab({ dog }) {
  const { hasRole } = useAuth();
  const hasStaffAccess = hasRole('staff');

  return (
    <div className="behavior-tab-content">
      <BehavioralAssessmentsSection behavioralAssessments={dog.BehavioralAssessments} />
      {!hasStaffAccess && (
        <div className="behavior-note">
          <p>Additional behavioral information may be available to Muttville staff and volunteers.</p>
        </div>
      )}
    </div>
  );
}

BehaviorTab.propTypes = {
  dog: PropTypes.object.isRequired
};

function WarningsTab({ dog }) {
  return (
    <div className="warnings-tab-content">
      <CompatibilityWarningsSection compatibilityWarnings={dog.CompatibilityWarnings} />
    </div>
  );
}

WarningsTab.propTypes = {
  dog: PropTypes.object.isRequired
};

function DocumentsTab({ dog }) {
  return (
    <div className="documents-tab-content">
      <AttachedDocumentsSection attachedDocuments={dog.AttachedDocuments} />
    </div>
  );
}

DocumentsTab.propTypes = {
  dog: PropTypes.object.isRequired
};

export function DogNotesSection({ dog }) {
  const [activeTab, setActiveTab] = useState('attributes');
  const tabs = ['attributes', 'personality', 'intake', 'medical', 'adoption', 'history', 'behavior', 'warnings', 'documents'];

  const tabComponents = {
    attributes: AttributesTab,
    personality: PersonalityTab,
    intake: IntakeTab,
    medical: MedicalTab,
    adoption: AdoptionTab,
    history: HistoryTab,
    behavior: BehaviorTab,
    warnings: WarningsTab,
    documents: DocumentsTab
  };

  const ActiveTabComponent = tabComponents[activeTab];

  return (
    <section className="dog-notes-section">
      <h2 className="dog-notes-title">Notes</h2>
      <div className="dog-notes-tabs">
        {tabs.map((tab) => (
          <button
            key={tab}
            type="button"
            className={`notes-tab${activeTab === tab ? ' notes-tab-active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      <div className="dog-notes-body">
        <ActiveTabComponent dog={dog} />
      </div>
    </section>
  );
}

DogNotesSection.propTypes = {
  dog: PropTypes.object.isRequired
};

