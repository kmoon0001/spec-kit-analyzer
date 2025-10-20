import React, { useState } from "react";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import styles from "./CitationManager.module.css";

interface Citation {
  id: string;
  type: "quote" | "reference" | "guideline" | "standard";
  content: string;
  source: string;
  page?: string;
  url?: string;
  dateAccessed?: string;
  discipline: "pt" | "ot" | "slp" | "all";
  category: "medicare" | "professional" | "research" | "legal";
  tags: string[];
  createdAt: string;
  lastUsed?: string;
}

interface CitationManagerProps {
  onSelect?: (citation: Citation) => void;
  onInsert?: (citation: Citation) => void;
  onClose?: () => void;
  className?: string;
}

const MOCK_CITATIONS: Citation[] = [
  {
    id: "medicare_ch15_quote_1",
    type: "quote",
    content:
      "Physical therapy services must be reasonable and necessary for the treatment of the individual's illness or injury.",
    source: "Medicare Benefits Policy Manual, Chapter 15",
    page: "Section 220.2",
    discipline: "pt",
    category: "medicare",
    tags: ["medical necessity", "physical therapy", "medicare"],
    createdAt: "2024-01-15",
    lastUsed: "2024-01-20",
  },
  {
    id: "apta_guideline_1",
    type: "guideline",
    content:
      "Physical therapists shall provide services only when they can reasonably expect to achieve beneficial outcomes.",
    source: "APTA Code of Ethics",
    page: "Principle 1A",
    discipline: "pt",
    category: "professional",
    tags: ["ethics", "outcomes", "apta"],
    createdAt: "2024-01-10",
    lastUsed: "2024-01-18",
  },
  {
    id: "cms_documentation_1",
    type: "reference",
    content:
      "Documentation must be legible, complete, and clearly establish medical necessity for each service provided.",
    source: "CMS Documentation Guidelines",
    page: "Section 2.1",
    discipline: "all",
    category: "medicare",
    tags: ["documentation", "medical necessity", "cms"],
    createdAt: "2024-01-12",
    lastUsed: "2024-01-19",
  },
  {
    id: "aota_standard_1",
    type: "standard",
    content:
      "Occupational therapy practitioners shall provide services in a manner that is consistent with accepted professional standards.",
    source: "AOTA Standards of Practice",
    page: "Standard I",
    discipline: "ot",
    category: "professional",
    tags: ["standards", "occupational therapy", "aota"],
    createdAt: "2024-01-08",
    lastUsed: "2024-01-17",
  },
  {
    id: "asha_guideline_1",
    type: "guideline",
    content:
      "Speech-language pathologists shall provide services that are evidence-based and culturally responsive.",
    source: "ASHA Scope of Practice",
    page: "Section 3.1",
    discipline: "slp",
    category: "professional",
    tags: ["evidence-based", "cultural competence", "asha"],
    createdAt: "2024-01-14",
    lastUsed: "2024-01-16",
  },
  {
    id: "therapy_cap_quote_1",
    type: "quote",
    content:
      "The therapy cap exceptions process requires documentation of medical necessity and functional improvement.",
    source: "Medicare Therapy Cap Guidelines",
    page: "Section 1833(g)",
    discipline: "all",
    category: "medicare",
    tags: ["therapy cap", "exceptions", "functional improvement"],
    createdAt: "2024-01-11",
    lastUsed: "2024-01-15",
  },
];

const TYPE_FILTERS = [
  { value: "all", label: "All Types", icon: "📚" },
  { value: "quote", label: "Quotes", icon: "💬" },
  { value: "reference", label: "References", icon: "📖" },
  { value: "guideline", label: "Guidelines", icon: "📋" },
  { value: "standard", label: "Standards", icon: "⭐" },
];

const CATEGORY_FILTERS = [
  { value: "all", label: "All Categories", icon: "📚" },
  { value: "medicare", label: "Medicare", icon: "🏛️" },
  { value: "professional", label: "Professional", icon: "👥" },
  { value: "research", label: "Research", icon: "🔬" },
  { value: "legal", label: "Legal", icon: "⚖️" },
];

const DISCIPLINE_FILTERS = [
  { value: "all", label: "All Disciplines", icon: "🏥" },
  { value: "pt", label: "Physical Therapy", icon: "🏃" },
  { value: "ot", label: "Occupational Therapy", icon: "🖐️" },
  { value: "slp", label: "Speech-Language Pathology", icon: "🗣️" },
];

export function CitationManager({
  onSelect,
  onInsert,
  onClose,
  className,
}: CitationManagerProps) {
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(
    null,
  );
  const [typeFilter, setTypeFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [disciplineFilter, setDisciplineFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [showAddForm, setShowAddForm] = useState(false);

  const filteredCitations = MOCK_CITATIONS.filter((citation) => {
    const matchesType = typeFilter === "all" || citation.type === typeFilter;
    const matchesCategory =
      categoryFilter === "all" || citation.category === categoryFilter;
    const matchesDiscipline =
      disciplineFilter === "all" ||
      citation.discipline === disciplineFilter ||
      citation.discipline === "all";
    const matchesSearch =
      searchTerm === "" ||
      citation.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
      citation.source.toLowerCase().includes(searchTerm.toLowerCase()) ||
      citation.tags.some((tag) =>
        tag.toLowerCase().includes(searchTerm.toLowerCase()),
      );

    return matchesType && matchesCategory && matchesDiscipline && matchesSearch;
  });

  const handleSelect = () => {
    if (selectedCitation && onSelect) {
      onSelect(selectedCitation);
    }
  };

  const handleInsert = () => {
    if (selectedCitation && onInsert) {
      onInsert(selectedCitation);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "quote":
        return "💬";
      case "reference":
        return "📖";
      case "guideline":
        return "📋";
      case "standard":
        return "⭐";
      default:
        return "📚";
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "medicare":
        return "🏛️";
      case "professional":
        return "👥";
      case "research":
        return "🔬";
      case "legal":
        return "⚖️";
      default:
        return "📚";
    }
  };

  const getDisciplineIcon = (discipline: string) => {
    switch (discipline) {
      case "pt":
        return "🏃";
      case "ot":
        return "🖐️";
      case "slp":
        return "🗣️";
      default:
        return "🏥";
    }
  };

  return (
    <Card
      title="📚 Citation Manager"
      subtitle="Manage quotes, references, and guidelines"
      className={className}
    >
      <div className={styles.citationManager}>
        {/* Filters */}
        <div className={styles.filtersSection}>
          <div className={styles.filterRow}>
            <div className={styles.filterGroup}>
              <label className={styles.filterLabel}>Type:</label>
              <div className={styles.filterButtons}>
                {TYPE_FILTERS.map((filter) => (
                  <button
                    key={filter.value}
                    className={`${styles.filterButton} ${typeFilter === filter.value ? styles.active : ""}`}
                    onClick={() => setTypeFilter(filter.value)}
                  >
                    <span className={styles.filterIcon}>{filter.icon}</span>
                    <span className={styles.filterText}>{filter.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className={styles.filterGroup}>
              <label className={styles.filterLabel}>Category:</label>
              <div className={styles.filterButtons}>
                {CATEGORY_FILTERS.map((filter) => (
                  <button
                    key={filter.value}
                    className={`${styles.filterButton} ${categoryFilter === filter.value ? styles.active : ""}`}
                    onClick={() => setCategoryFilter(filter.value)}
                  >
                    <span className={styles.filterIcon}>{filter.icon}</span>
                    <span className={styles.filterText}>{filter.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className={styles.filterRow}>
            <div className={styles.filterGroup}>
              <label className={styles.filterLabel}>Discipline:</label>
              <div className={styles.filterButtons}>
                {DISCIPLINE_FILTERS.map((filter) => (
                  <button
                    key={filter.value}
                    className={`${styles.filterButton} ${disciplineFilter === filter.value ? styles.active : ""}`}
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
                placeholder="Search citations..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={styles.searchInput}
              />
            </div>
          </div>
        </div>

        {/* Citation List */}
        <div className={styles.citationList}>
          <div className={styles.listHeader}>
            <span className={styles.headerText}>
              {filteredCitations.length} citation
              {filteredCitations.length !== 1 ? "s" : ""} found
            </span>
            <Button
              variant="outline"
              onClick={() => setShowAddForm(!showAddForm)}
            >
              {showAddForm ? "Cancel" : "+ Add Citation"}
            </Button>
          </div>

          <div className={styles.citationItems}>
            {filteredCitations.map((citation) => (
              <div
                key={citation.id}
                className={`${styles.citationItem} ${selectedCitation?.id === citation.id ? styles.selected : ""}`}
                onClick={() => setSelectedCitation(citation)}
              >
                <div className={styles.citationHeader}>
                  <div className={styles.citationTitle}>
                    <span className={styles.typeIcon}>
                      {getTypeIcon(citation.type)}
                    </span>
                    <span className={styles.categoryIcon}>
                      {getCategoryIcon(citation.category)}
                    </span>
                    <span className={styles.disciplineIcon}>
                      {getDisciplineIcon(citation.discipline)}
                    </span>
                    <span className={styles.citationType}>
                      {citation.type.toUpperCase()}
                    </span>
                  </div>
                  <div className={styles.citationMeta}>
                    <span className={styles.lastUsed}>
                      {citation.lastUsed
                        ? `Used: ${new Date(citation.lastUsed).toLocaleDateString()}`
                        : "Never used"}
                    </span>
                  </div>
                </div>

                <div className={styles.citationContent}>
                  <div className={styles.citationText}>
                    "{citation.content}"
                  </div>
                  <div className={styles.citationSource}>
                    <strong>Source:</strong> {citation.source}
                    {citation.page && <span> (Page {citation.page})</span>}
                  </div>
                </div>

                <div className={styles.citationTags}>
                  {citation.tags.map((tag) => (
                    <span key={tag} className={styles.tag}>
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className={styles.actionsSection}>
          <div className={styles.selectedInfo}>
            {selectedCitation ? (
              <div className={styles.selectedCitation}>
                <span className={styles.selectedLabel}>Selected:</span>
                <span className={styles.selectedName}>
                  {selectedCitation.source}
                </span>
              </div>
            ) : (
              <span className={styles.noSelection}>No citation selected</span>
            )}
          </div>

          <div className={styles.actionButtons}>
            <Button
              variant="outline"
              onClick={() => setSelectedCitation(null)}
              disabled={!selectedCitation}
            >
              Clear Selection
            </Button>
            <Button
              variant="primary"
              onClick={handleSelect}
              disabled={!selectedCitation}
            >
              Select Citation
            </Button>
            <Button
              variant="primary"
              onClick={handleInsert}
              disabled={!selectedCitation}
            >
              Insert into Document
            </Button>
            {onClose && (
              <Button variant="outline" onClick={onClose}>
                Close
              </Button>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
