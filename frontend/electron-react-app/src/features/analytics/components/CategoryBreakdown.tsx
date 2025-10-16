import React from 'react';
import styles from './CategoryBreakdown.module.css';

interface CategoryBreakdownProps {
  categories: Array<{
    name: string;
    score: number;
    color: string;
  }>;
}

export const CategoryBreakdown: React.FC<CategoryBreakdownProps> = ({ categories }) => {
  return (
    <div className={styles.container}>
      <h3 className={styles.title}>📋 Category Breakdown</h3>
      <div className={styles.categoryList}>
        {categories.map((category) => (
          <div key={category.name} className={styles.categoryItem}>
            <div className={styles.categoryName}>{category.name}</div>
            <div className={styles.progressContainer}>
              <div className={styles.progressBar}>
                <div
                  className={styles.progressFill}
                  style={{
                    width: `${category.score}%`,
                    backgroundColor: category.color
                  }}
                />
              </div>
              <div className={styles.scoreLabel} style={{ color: category.color }}>
                {category.score}%
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};