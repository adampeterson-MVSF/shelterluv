import { useState } from 'react';
import PropTypes from 'prop-types';
import { MedicalHistorySections } from './MedicalHistorySections';
import { EventHistorySection } from './EventHistorySection';
import { WeightHistorySection } from './WeightHistorySection';
import { CategoryHistorySection } from './CategoryHistorySection';
import { BehavioralAssessmentsSection } from './BehavioralAssessmentsSection';
import { CompatibilityWarningsSection } from './CompatibilityWarningsSection';
import { AttachedDocumentsSection } from './AttachedDocumentsSection';
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

  if (!hasNotes) {
    return <p className="notes-paragraph">No personality notes available.</p>;
  }

  return (
    <div className="personality-notes">
      <p className="notes-paragraph">{dog.PersonalityNotes}</p>
    </div>
  );
}

PersonalityTab.propTypes = {
  dog: PropTypes.object.isRequired
};

function MedicalTab({ dog }) {
  const { hasMedicalHistory, hasMedicalNotes } = checkMedicalInfo(dog);

  if (!hasMedicalHistory && !hasMedicalNotes) {
    return <p className="notes-paragraph">No medical information available.</p>;
  }

  return (
    <div className="medical-notes">
      {hasMedicalNotes && (
        <div className="medical-section">
          <h3 className="section-title">📝 Medical Notes</h3>
          <div className="section-content">
            <p className="notes-paragraph">{dog.MedicalNotes}</p>
          </div>
        </div>
      )}
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
  const { user } = useContext(AuthContext);
  const hasStaffAccess = user && (user.role === 'staff' || user.role === 'volunteer' || user.role === 'admin');

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

