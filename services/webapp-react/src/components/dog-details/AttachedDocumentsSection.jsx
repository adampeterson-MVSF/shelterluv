import PropTypes from 'prop-types';
import './AttachedDocumentsSection.css';

function formatDocumentDate(dateString) {
  if (!dateString) return 'Unknown date';
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  } catch {
    return dateString;
  }
}

function getFileTypeIcon(fileType) {
  const iconMap = {
    'photo': '📸',
    'document': '📄',
    'pdf': '📕',
    'certificate': '🏆',
    'contract': '📋',
    'medical': '🏥',
    'report': '📊'
  };

  // Try to match the file type, default to document
  const type = fileType?.toLowerCase();
  return iconMap[type] || iconMap.document;
}

function getFileExtension(filename) {
  if (!filename) return '';
  const parts = filename.split('.');
  return parts.length > 1 ? parts[parts.length - 1].toUpperCase() : '';
}

function groupAndSortDocuments(attachedDocuments) {
  // Group documents by type
  const groupedDocuments = attachedDocuments.reduce((acc, doc) => {
    const type = doc.file_type || 'Other';
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(doc);
    return acc;
  }, {});

  // Sort documents within each group by upload date (newest first)
  Object.keys(groupedDocuments).forEach(type => {
    groupedDocuments[type].sort((a, b) => {
      if (!a.upload_date && !b.upload_date) return 0;
      if (!a.upload_date) return 1;
      if (!b.upload_date) return -1;
      return new Date(b.upload_date) - new Date(a.upload_date);
    });
  });

  return groupedDocuments;
}

function renderDocumentGroups(groupedDocuments) {
  const groupOrder = ['Medical', 'Certificate', 'Contract', 'Photo', 'Report'];

  return (
    <>
      {/* Display groups in a logical order */}
      {groupOrder.map(groupType => {
        if (groupedDocuments[groupType]) {
          const titles = {
            'Medical': '🏥 Medical Records',
            'Certificate': '🏆 Certificates',
            'Contract': '📋 Contracts & Agreements',
            'Photo': '📸 Photos',
            'Report': '📊 Reports'
          };
          return (
            <DocumentGroup
              key={groupType}
              title={titles[groupType]}
              documents={groupedDocuments[groupType]}
            />
          );
        }
        return null;
      })}

      {/* Any remaining document types */}
      {Object.entries(groupedDocuments)
        .filter(([type]) => !groupOrder.includes(type))
        .map(([type, documents]) => (
          <DocumentGroup
            key={type}
            title={`${getFileTypeIcon(type)} ${type} Documents`}
            documents={documents}
          />
        ))
      }
    </>
  );
}

function DocumentCard({ document }) {
  const handleDownload = () => {
    if (document.url) {
      window.open(document.url, '_blank');
    }
  };

  const fileExtension = getFileExtension(document.filename);

  return (
    <div className="document-card">
      <div className="document-header">
        <div className="document-icon">
          {getFileTypeIcon(document.file_type)}
        </div>
        <div className="document-info">
          <h4 className="document-filename">{document.filename}</h4>
          <div className="document-meta">
            <span className="document-type">{document.file_type || 'Document'}</span>
            {fileExtension && (
              <>
                <span className="document-separator">•</span>
                <span className="document-extension">{fileExtension}</span>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="document-content">
        {document.description && (
          <p className="document-description">{document.description}</p>
        )}

        <div className="document-footer">
          <span className="document-date">
            Uploaded {formatDocumentDate(document.upload_date)}
          </span>
          {document.url && (
            <button
              type="button"
              className="document-download-btn"
              onClick={handleDownload}
              title={`Download ${document.filename}`}
            >
              📥 View/Download
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

DocumentCard.propTypes = {
  document: PropTypes.shape({
    filename: PropTypes.string,
    file_type: PropTypes.string,
    upload_date: PropTypes.string,
    description: PropTypes.string,
    url: PropTypes.string
  }).isRequired
};

function DocumentGroup({ title, documents }) {
  if (!documents || documents.length === 0) return null;

  return (
    <div className="document-group">
      <h3 className="document-group-title">{title}</h3>
      <div className="document-grid">
        {documents.map((document, index) => (
          <DocumentCard
            key={`${document.filename}-${document.upload_date}-${index}`}
            document={document}
          />
        ))}
      </div>
    </div>
  );
}

DocumentGroup.propTypes = {
  title: PropTypes.string.isRequired,
  documents: PropTypes.array.isRequired
};

export function AttachedDocumentsSection({ attachedDocuments }) {
  if (!attachedDocuments || attachedDocuments.length === 0) {
    return (
      <section className="attached-documents-section">
        <h2 className="section-title">📎 Attached Documents</h2>
        <div className="no-data-message">
          <p>No documents attached to this dog&apos;s record.</p>
        </div>
      </section>
    );
  }

  const groupedDocuments = groupAndSortDocuments(attachedDocuments);

  return (
    <section className="attached-documents-section">
      <h2 className="section-title">📎 Attached Documents</h2>

      <div className="documents-intro">
        <p>
          Important documents related to this dog&apos;s care, medical history, and adoption process.
          Click &quot;View/Download&quot; to access each document.
        </p>
      </div>

      <div className="documents-content">
        {renderDocumentGroups(groupedDocuments)}
      </div>
    </section>
  );
}

AttachedDocumentsSection.propTypes = {
  attachedDocuments: PropTypes.arrayOf(
    PropTypes.shape({
      filename: PropTypes.string,
      file_type: PropTypes.string,
      upload_date: PropTypes.string,
      description: PropTypes.string,
      url: PropTypes.string
    })
  )
};
