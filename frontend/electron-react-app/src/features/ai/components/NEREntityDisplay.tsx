import React from 'react';
import styles from './NEREntityDisplay.module.css';

interface NEREntity {
  text: string;
  label: string;
  confidence: number;
  start: number;
  end: number;
  source_model?: string;
}

interface NEREntityDisplayProps {
  entities: NEREntity[];
  originalText: string;
  showModelSources?: boolean;
  highlightInText?: boolean;
}

export const NEREntityDisplay: React.FC<NEREntityDisplayProps> = ({
  entities,
  originalText,
  showModelSources = false,
  highlightInText = false,
}) => {
  const getEntityColor = (label: string) => {
    const colorMap: Record<string, string> = {
      'PERSON': '#007acc',
      'CONDITION': '#dc3545',
      'MEDICATION': '#28a745',
      'PROCEDURE': '#ffc107',
      'ANATOMY': '#17a2b8',
      'SYMPTOM': '#e83e8c',
      'TREATMENT': '#6f42c1',
      'DEVICE': '#fd7e14',
      'DOSAGE': '#20c997',
      'FREQUENCY': '#6610f2',
    };
    return colorMap[label] || '#6c757d';
  };

  const renderHighlightedText = () => {
    if (!highlightInText || entities.length === 0) {
      return <div className={styles.plainText}>{originalText}</div>;
    }

    // Sort entities by start position
    const sortedEntities = [...entities].sort((a, b) => a.start - b.start);

    let lastIndex = 0;
    const parts: React.ReactNode[] = [];

    sortedEntities.forEach((entity, index) => {
      // Add text before entity
      if (entity.start > lastIndex) {
        parts.push(
          <span key={`text-${index}`}>
            {originalText.slice(lastIndex, entity.start)}
          </span>
        );
      }

      // Add highlighted entity
      parts.push(
        <span
          key={`entity-${index}`}
          className={styles.highlightedEntity}
          style={{ backgroundColor: getEntityColor(entity.label) + '20' }}
          title={`${entity.label} (${Math.round(entity.confidence * 100)}%)`}
        >
          {entity.text}
        </span>
      );

      lastIndex = entity.end;
    });

    // Add remaining text
    if (lastIndex < originalText.length) {
      parts.push(
        <span key="text-end">
          {originalText.slice(lastIndex)}
        </span>
      );
    }

    return <div className={styles.highlightedText}>{parts}</div>;
  };

  const groupedEntities = entities.reduce((groups, entity) => {
    const key = entity.label;
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(entity);
    return groups;
  }, {} as Record<string, NEREntity[]>);

  return (
    <div className={styles.container}>
      {highlightInText && (
        <div className={styles.textSection}>
          <h4 className={styles.sectionTitle}>📝 Text with Highlighted Entities</h4>
          {renderHighlightedText()}
        </div>
      )}

      <div className={styles.entitiesSection}>
        <h4 className={styles.sectionTitle}>
          🏷️ Extracted Entities ({entities.length})
        </h4>

        {Object.keys(groupedEntities).length === 0 ? (
          <div className={styles.noEntities}>
            No clinical entities detected in this text.
          </div>
        ) : (
          <div className={styles.entityGroups}>
            {Object.entries(groupedEntities).map(([label, entityList]) => (
              <div key={label} className={styles.entityGroup}>
                <div
                  className={styles.groupHeader}
                  style={{ borderLeftColor: getEntityColor(label) }}
                >
                  <span className={styles.groupLabel}>{label}</span>
                  <span className={styles.groupCount}>({entityList.length})</span>
                </div>

                <div className={styles.entityList}>
                  {entityList.map((entity, index) => (
                    <div key={index} className={styles.entityItem}>
                      <div className={styles.entityText}>"{entity.text}"</div>
                      <div className={styles.entityMeta}>
                        <span className={styles.confidence}>
                          {Math.round(entity.confidence * 100)}%
                        </span>
                        {showModelSources && entity.source_model && (
                          <span className={styles.sourceModel}>
                            {entity.source_model}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};