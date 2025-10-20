import React, { useState } from 'react';
import { Button } from '../../../components/ui/Button';
import { Card } from '../../../components/ui/Card';
import { StatusChip } from '../../../components/ui/StatusChip';

import styles from './LibrarySelectionDialog.module.css';

interface RubricItem {
    id: string;
    name: string;
    description: string;
    discipline: 'pt' | 'ot' | 'slp' | 'all';
    category: 'medicare' | 'professional' | 'custom';
    lastModified: string;
    isDefault: boolean;
}

interface LibrarySelectionDialogProps {
    onSelect?: (rubric: RubricItem) => void;
    onClose?: () => void;
    className?: string;
}

const MOCK_RUBRICS: RubricItem[] = [
    {
        id: 'medicare_benefits_policy_manual_ch15',
        name: 'Medicare Benefits Policy Manual - Chapter 15',
        description: 'Comprehensive Medicare coverage policies for medical services including therapy requirements',
        discipline: 'all',
        category: 'medicare',
        lastModified: '2024-01-15',
        isDefault: true
    },
    {
        id: 'medicare_part_b_therapy_guidelines',
        name: 'Medicare Part B Outpatient Therapy Guidelines',
        description: 'Specific guidelines for outpatient therapy services under Medicare Part B',
        discipline: 'all',
        category: 'medicare',
        lastModified: '2024-01-10',
        isDefault: true
    },
    {
        id: 'cms_1500_documentation_requirements',
        name: 'CMS-1500 Documentation Requirements',
        description: 'Documentation standards required for CMS-1500 claim forms',
        discipline: 'all',
        category: 'medicare',
        lastModified: '2024-01-08',
        isDefault: true
    },
    {
        id: 'apta_pt_guidelines',
        name: 'Physical Therapy - APTA Guidelines',
        description: 'American Physical Therapy Association clinical practice guidelines',
        discipline: 'pt',
        category: 'professional',
        lastModified: '2024-01-12',
        isDefault: true
    },
    {
        id: 'aota_ot_standards',
        name: 'Occupational Therapy - AOTA Standards',
        description: 'American Occupational Therapy Association practice standards',
        discipline: 'ot',
        category: 'professional',
        lastModified: '2024-01-14',
        isDefault: true
    },
    {
        id: 'asha_slp_guidelines',
        name: 'Speech-Language Pathology - ASHA Guidelines',
        description: 'American Speech-Language-Hearing Association clinical guidelines',
        discipline: 'slp',
        category: 'professional',
        lastModified: '2024-01-11',
        isDefault: true
    },
    {
        id: 'custom_therapy_cap_guidelines',
        name: 'Custom Therapy Cap Guidelines',
        description: 'Customized guidelines for therapy cap exceptions and documentation',
        discipline: 'all',
        category: 'custom',
        lastModified: '2024-01-05',
        isDefault: false
    },
    {
        id: 'custom_skilled_therapy_standards',
        name: 'Custom Skilled Therapy Standards',
        description: 'Organization-specific standards for skilled therapy documentation',
        discipline: 'all',
        category: 'custom',
        lastModified: '2024-01-03',
        isDefault: false
    }
];

const CATEGORY_FILTERS = [
    { value: 'all', label: 'All Categories', icon: '📚' },
    { value: 'medicare', label: 'Medicare Guidelines', icon: '🏛️' },
    { value: 'professional', label: 'Professional Standards', icon: '👥' },
    { value: 'custom', label: 'Custom Rubrics', icon: '⚙️' }
];

const DISCIPLINE_FILTERS = [
    { value: 'all', label: 'All Disciplines', icon: '🏥' },
    { value: 'pt', label: 'Physical Therapy', icon: '🏃' },
    { value: 'ot', label: 'Occupational Therapy', icon: '🖐️' },
    { value: 'slp', label: 'Speech-Language Pathology', icon: '🗣️' }
];

export function LibrarySelectionDialog({ onSelect, onClose, className }: LibrarySelectionDialogProps) {
    const [selectedRubric, setSelectedRubric] = useState<RubricItem | null>(null);
    const [categoryFilter, setCategoryFilter] = useState('all');
    const [disciplineFilter, setDisciplineFilter] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');

    const filteredRubrics = MOCK_RUBRICS.filter(rubric => {
        const matchesCategory = categoryFilter === 'all' || rubric.category === categoryFilter;
        const matchesDiscipline = disciplineFilter === 'all' || rubric.discipline === disciplineFilter || rubric.discipline === 'all';
        const matchesSearch = searchTerm === '' ||
            rubric.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            rubric.description.toLowerCase().includes(searchTerm.toLowerCase());

        return matchesCategory && matchesDiscipline && matchesSearch;
    });

    const handleSelect = () => {
        if (selectedRubric && onSelect) {
            onSelect(selectedRubric);
        }
    };

    const getCategoryIcon = (category: string) => {
        switch (category) {
            case 'medicare': return '🏛️';
            case 'professional': return '👥';
            case 'custom': return '⚙️';
            default: return '📚';
        }
    };

    const getDisciplineIcon = (discipline: string) => {
        switch (discipline) {
            case 'pt': return '🏃';
            case 'ot': return '🖐️';
            case 'slp': return '🗣️';
            default: return '🏥';
        }
    };

    return (
        <div className={styles.dialogOverlay}>
            <Card title="📚 Rubric Library" subtitle="Select from pre-loaded compliance rubrics" className={className}>
                <div className={styles.dialogContent}>
                    {/* Filters */}
                    <div className={styles.filtersSection}>
                        <div className={styles.filterGroup}>
                            <label className={styles.filterLabel}>Category:</label>
                            <div className={styles.filterButtons}>
                                {CATEGORY_FILTERS.map(filter => (
                                    <button
                                        key={filter.value}
                                        className={`${styles.filterButton} ${categoryFilter === filter.value ? styles.active : ''}`}
                                        onClick={() => setCategoryFilter(filter.value)}
                                    >
                                        <span className={styles.filterIcon}>{filter.icon}</span>
                                        <span className={styles.filterText}>{filter.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className={styles.filterGroup}>
                            <label className={styles.filterLabel}>Discipline:</label>
                            <div className={styles.filterButtons}>
                                {DISCIPLINE_FILTERS.map(filter => (
                                    <button
                                        key={filter.value}
                                        className={`${styles.filterButton} ${disciplineFilter === filter.value ? styles.active : ''}`}
                                        onClick={() => setDisciplineFilter(filter.value)}
                                    >
                                        <span className={styles.filterIcon}>{filter.icon}</span>
                                        <span className={styles.filterText}>{filter.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className={styles.searchGroup}>
                            <label className={styles.filterLabel}>Search:</label>
                            <input
                                type="text"
                                placeholder="Search rubrics..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className={styles.searchInput}
                            />
                        </div>
                    </div>

                    {/* Rubric List */}
                    <div className={styles.rubricList}>
                        <div className={styles.listHeader}>
                            <span className={styles.headerText}>
                                {filteredRubrics.length} rubric{filteredRubrics.length !== 1 ? 's' : ''} found
                            </span>
                        </div>

                        <div className={styles.rubricItems}>
                            {filteredRubrics.map(rubric => (
                                <div
                                    key={rubric.id}
                                    className={`${styles.rubricItem} ${selectedRubric?.id === rubric.id ? styles.selected : ''}`}
                                    onClick={() => setSelectedRubric(rubric)}
                                >
                                    <div className={styles.rubricHeader}>
                                        <div className={styles.rubricTitle}>
                                            <span className={styles.categoryIcon}>{getCategoryIcon(rubric.category)}</span>
                                            <span className={styles.disciplineIcon}>{getDisciplineIcon(rubric.discipline)}</span>
                                            <span className={styles.rubricName}>{rubric.name}</span>
                                            {rubric.isDefault && (
                                                <StatusChip label="Default" status="ready" />
                                            )}
                                        </div>
                                        <div className={styles.rubricMeta}>
                                            <span className={styles.lastModified}>
                                                Modified: {new Date(rubric.lastModified).toLocaleDateString()}
                                            </span>
                                        </div>
                                    </div>

                                    <div className={styles.rubricDescription}>
                                        {rubric.description}
                                    </div>

                                    <div className={styles.rubricTags}>
                                        <span className={styles.tag}>{rubric.category.toUpperCase()}</span>
                                        <span className={styles.tag}>{rubric.discipline.toUpperCase()}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Actions */}
                    <div className={styles.actionsSection}>
                        <div className={styles.selectedInfo}>
                            {selectedRubric ? (
                                <div className={styles.selectedRubric}>
                                    <span className={styles.selectedLabel}>Selected:</span>
                                    <span className={styles.selectedName}>{selectedRubric.name}</span>
                                </div>
                            ) : (
                                <span className={styles.noSelection}>No rubric selected</span>
                            )}
                        </div>

                        <div className={styles.actionButtons}>
                            <Button
                                variant="outline"
                                onClick={onClose}
                            >
                                Cancel
                            </Button>
                            <Button
                                variant="primary"
                                onClick={handleSelect}
                                disabled={!selectedRubric}
                            >
                                Select Rubric
                            </Button>
                        </div>
                    </div>
                </div>
            </Card>
        </div>
    );
}
