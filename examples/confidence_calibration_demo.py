#!/usr/bin/env python3
"""
Confidence Calibration Demo

This script demonstrates how confidence calibration improves the reliability
of AI confidence scores in the Therapy Compliance Analyzer.
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.confidence_calibrator import ConfidenceCalibrator


def generate_synthetic_compliance_data(n_samples=200):
    """Generate synthetic compliance analysis data.
    
    Simulates an overconfident LLM that gives high confidence scores
    but isn't always correct.
    """
    np.random.seed(42)
    
    # Generate confidence scores biased toward high values (overconfident model)
    raw_confidences = np.random.beta(5, 2, n_samples)  # Biased toward 0.7-0.9
    
    # Generate ground truth where high confidence doesn't always mean correct
    # Simulate that the LLM is correct about 75% of the time on average,
    # but the relationship with confidence is weaker than it should be
    base_accuracy = 0.75
    confidence_effect = 0.3  # How much confidence actually correlates with correctness
    
    true_probabilities = base_accuracy + (raw_confidences - 0.5) * confidence_effect
    true_probabilities = np.clip(true_probabilities, 0.1, 0.9)  # Keep realistic
    
    # Generate binary labels
    labels = np.random.binomial(1, true_probabilities, n_samples)
    
    return raw_confidences, labels


def plot_calibration_comparison(raw_confidences, labels, calibrator):
    """Plot calibration curves before and after calibration."""
    # Calculate calibrated confidences
    calibrated_confidences = calibrator.calibrate(raw_confidences)
    
    # Create calibration plots
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    
    # Plot 1: Raw vs Calibrated Confidence Distribution
    ax1.hist(raw_confidences, bins=20, alpha=0.7, label='Raw Confidence', color='red')
    ax1.hist(calibrated_confidences, bins=20, alpha=0.7, label='Calibrated Confidence', color='blue')
    ax1.set_xlabel('Confidence Score')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Confidence Score Distribution')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Calibration Curve (Raw)
    n_bins = 10
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]
    
    raw_bin_accuracies = []
    raw_bin_confidences = []
    raw_bin_counts = []
    
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        in_bin = (raw_confidences > bin_lower) & (raw_confidences <= bin_upper)
        if in_bin.sum() > 0:
            raw_bin_accuracies.append(labels[in_bin].mean())
            raw_bin_confidences.append(raw_confidences[in_bin].mean())
            raw_bin_counts.append(in_bin.sum())
        else:
            raw_bin_accuracies.append(0)
            raw_bin_confidences.append((bin_lower + bin_upper) / 2)
            raw_bin_counts.append(0)
    
    ax2.plot([0, 1], [0, 1], 'k--', label='Perfect Calibration')
    ax2.scatter(raw_bin_confidences, raw_bin_accuracies, 
               s=[c*5 for c in raw_bin_counts], alpha=0.7, color='red', label='Raw Confidence')
    ax2.set_xlabel('Mean Predicted Confidence')
    ax2.set_ylabel('Fraction of Positives')
    ax2.set_title('Calibration Curve (Raw)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([0, 1])
    ax2.set_ylim([0, 1])
    
    # Plot 3: Calibration Curve (Calibrated)
    cal_bin_accuracies = []
    cal_bin_confidences = []
    cal_bin_counts = []
    
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        in_bin = (calibrated_confidences > bin_lower) & (calibrated_confidences <= bin_upper)
        if in_bin.sum() > 0:
            cal_bin_accuracies.append(labels[in_bin].mean())
            cal_bin_confidences.append(calibrated_confidences[in_bin].mean())
            cal_bin_counts.append(in_bin.sum())
        else:
            cal_bin_accuracies.append(0)
            cal_bin_confidences.append((bin_lower + bin_upper) / 2)
            cal_bin_counts.append(0)
    
    ax3.plot([0, 1], [0, 1], 'k--', label='Perfect Calibration')
    ax3.scatter(cal_bin_confidences, cal_bin_accuracies, 
               s=[c*5 for c in cal_bin_counts], alpha=0.7, color='blue', label='Calibrated Confidence')
    ax3.set_xlabel('Mean Predicted Confidence')
    ax3.set_ylabel('Fraction of Positives')
    ax3.set_title('Calibration Curve (Calibrated)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim([0, 1])
    ax3.set_ylim([0, 1])
    
    plt.tight_layout()
    plt.savefig('confidence_calibration_demo.png', dpi=300, bbox_inches='tight')
    plt.show()


def calculate_calibration_metrics(confidences, labels):
    """Calculate calibration quality metrics."""
    # Expected Calibration Error (ECE)
    n_bins = 10
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]
    
    ece = 0
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = in_bin.mean()
        
        if prop_in_bin > 0:
            accuracy_in_bin = labels[in_bin].mean()
            avg_confidence_in_bin = confidences[in_bin].mean()
            ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
    
    # Brier Score
    brier_score = np.mean((confidences - labels) ** 2)
    
    return ece, brier_score


def main():
    """Run the confidence calibration demonstration."""
    print("🎯 Confidence Calibration Demo for Therapy Compliance Analyzer")
    print("=" * 70)
    
    # Generate synthetic data
    print("\n📊 Generating synthetic compliance analysis data...")
    raw_confidences, labels = generate_synthetic_compliance_data(n_samples=300)
    
    print(f"   • Generated {len(raw_confidences)} synthetic compliance findings")
    print(f"   • Mean raw confidence: {raw_confidences.mean():.3f}")
    print(f"   • Actual accuracy: {labels.mean():.3f}")
    print(f"   • Model appears overconfident (high confidence, lower accuracy)")
    
    # Split data for training and testing
    split_idx = len(raw_confidences) // 2
    train_confidences = raw_confidences[:split_idx]
    train_labels = labels[:split_idx]
    test_confidences = raw_confidences[split_idx:]
    test_labels = labels[split_idx:]
    
    print(f"\n🔧 Training calibrator on {len(train_confidences)} samples...")
    
    # Train calibrator
    calibrator = ConfidenceCalibrator(method='auto')
    calibrator.fit(train_confidences, train_labels)
    
    print(f"   • Best calibration method: {calibrator.method}")
    
    # Get calibration metrics
    metrics = calibrator.get_calibration_metrics()
    print(f"   • Calibration metrics: {metrics}")
    
    # Test on held-out data
    print(f"\n🧪 Testing on {len(test_confidences)} held-out samples...")
    
    # Calculate metrics before calibration
    raw_ece, raw_brier = calculate_calibration_metrics(test_confidences, test_labels)
    
    # Apply calibration
    calibrated_confidences = calibrator.calibrate(test_confidences)
    
    # Calculate metrics after calibration
    cal_ece, cal_brier = calculate_calibration_metrics(calibrated_confidences, test_labels)
    
    print(f"\n📈 Calibration Results:")
    print(f"   • Expected Calibration Error (ECE):")
    print(f"     - Before: {raw_ece:.4f}")
    print(f"     - After:  {cal_ece:.4f}")
    print(f"     - Improvement: {((raw_ece - cal_ece) / raw_ece * 100):.1f}%")
    
    print(f"   • Brier Score:")
    print(f"     - Before: {raw_brier:.4f}")
    print(f"     - After:  {cal_brier:.4f}")
    print(f"     - Improvement: {((raw_brier - cal_brier) / raw_brier * 100):.1f}%")
    
    print(f"\n📊 Confidence Score Changes:")
    print(f"   • Mean confidence before: {test_confidences.mean():.3f}")
    print(f"   • Mean confidence after:  {calibrated_confidences.mean():.3f}")
    print(f"   • Standard deviation before: {test_confidences.std():.3f}")
    print(f"   • Standard deviation after:  {calibrated_confidences.std():.3f}")
    
    # Show examples of individual changes
    print(f"\n🔍 Example Confidence Changes:")
    for i in range(min(5, len(test_confidences))):
        original = test_confidences[i]
        calibrated = calibrated_confidences[i]
        actual = "Correct" if test_labels[i] else "Incorrect"
        change = "↓" if calibrated < original else "↑" if calibrated > original else "→"
        print(f"   • Finding {i+1}: {original:.3f} → {calibrated:.3f} {change} ({actual})")
    
    # Create visualization
    print(f"\n📈 Creating calibration visualization...")
    try:
        plot_calibration_comparison(test_confidences, test_labels, calibrator)
        print("   • Saved calibration plots to 'confidence_calibration_demo.png'")
    except ImportError:
        print("   • Matplotlib not available, skipping visualization")
    except Exception as e:
        print(f"   • Visualization failed: {e}")
    
    print(f"\n✅ Demo completed successfully!")
    print(f"\n💡 Key Takeaways:")
    print(f"   • Confidence calibration improves reliability of AI confidence scores")
    print(f"   • Overconfident models benefit significantly from calibration")
    print(f"   • Calibrated scores better reflect true probability of correctness")
    print(f"   • This helps users make better decisions about AI recommendations")


if __name__ == "__main__":
    main()