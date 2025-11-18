import { useState } from 'react';
import PropTypes from 'prop-types';
import {
  shapeBasicAttributes,
  shapeMicrochipAttributes,
  shapeAlteredAttributes,
  shapeIntakeAttributes,
  shapeAdoptionAttributes
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
  const microchipItems = shapeMicrochipAttributes(dog);
  const alteredItems = shapeAlteredAttributes(dog);

  // Get all published attributes in a single list
  const allPublishedAttributes = (dog.attributes?.raw || [])
    .filter(attr => attr.publish === 'Yes')
    .map(attr => attr.attributeName);

  return (
    <>
      <ul className="attributes-list">
        {basicItems.map((text, index) => (
          <li key={index}>{text}</li>
        ))}
      </ul>

      <AttributeSection title="Microchip" items={microchipItems} keyPrefix="chip" />
      <AttributeSection title="Altered Status" items={alteredItems} keyPrefix="altered" />

      {/* All published attributes in a single bulleted list */}
      {allPublishedAttributes.length > 0 && (
        <div className="attributes-section">
          <h3 className="attributes-section-title">Attributes</h3>
          <ul className="attributes-list">
            {allPublishedAttributes.map((attributeName, i) => (
              <li key={`attribute-${i}`}>
                {attributeName}
              </li>
            ))}
          </ul>
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
      {/* Intake notes are now shown in the personality/content section */}
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
  // For now, personality information is in content.description
  // TODO: Structure this better when we have separate personality fields
  const description = dog.content?.description || '';
  const hasContent = description.trim().length > 0;

  if (!hasContent) {
    return <p className="notes-paragraph">No personality information available.</p>;
  }

  return (
    <div className="personality-notes">
      <div className="personality-notes-section">
        <h4 style={{ fontWeight: 'bold', marginBottom: '8px' }}>About {dog.name}</h4>
          <div style={{ lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
          {description}
        </div>
        </div>
    </div>
  );
}

PersonalityTab.propTypes = {
  dog: PropTypes.object.isRequired
};

function MedicalTab({ dog }) {
  const hasMicrochips = dog.medical?.microchips && dog.medical.microchips.length > 0;
  const hasMedicalContent = dog.content?.description && (
    dog.content.description.includes('Medical') ||
    dog.content.description.includes('Vet') ||
    dog.content.description.includes('vaccin')
  );

  if (!hasMicrochips && !hasMedicalContent) {
    return <p className="notes-paragraph">No medical information available.</p>;
  }

  return (
    <div className="medical-notes">
      {/* Microchip Information */}
      {hasMicrochips && (
        <div className="medical-section">
          <h3 className="section-title">🆔 Microchip Information</h3>
          <div className="section-content">
            <ul className="attributes-list">
              {dog.medical.microchips.map((chip, index) => (
                <li key={index}>
                  <strong>{chip.id}:</strong>
                  {chip.issuer && ` ${chip.issuer}`}
                  {chip.implantedAt && ` (Implanted: ${new Date(chip.implantedAt).toLocaleDateString()})`}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Additional medical content */}
      {hasMedicalContent && (
        <div className="medical-section">
          <h3 className="section-title">📋 Medical Notes</h3>
          <div className="section-content">
            <div style={{ lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
              {dog.content.description}
              </div>
          </div>
        </div>
      )}

      {/* TODO: Add structured medical data sections when medical schema is expanded */}





    </div>
  );
}

MedicalTab.propTypes = {
  dog: PropTypes.object.isRequired
};


export function DogNotesSection({ dog }) {
  const [activeTab, setActiveTab] = useState('attributes');
  const tabs = ['attributes', 'personality', 'intake', 'medical', 'adoption'];

  const tabComponents = {
    attributes: AttributesTab,
    personality: PersonalityTab,
    intake: IntakeTab,
    medical: MedicalTab,
    adoption: AdoptionTab
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

