#!/usr/bin/env python3
"""
ML Training Pipeline Demo

This script demonstrates the complete machine learning training pipeline
that replaces the placeholder implementation, showing how user feedback
is used to continuously improve confidence calibration.
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ml.trainer import MLTrainingPipeline
from src.core.calibration_trainer import CalibrationTrainer, FeedbackCollector
from src.core.ml_scheduler import MLScheduler


async def simulate_user_feedback_collection():
    """Simulate collecting user feedback on compliance findings."""
    print("📝 Simulating user feedback collection...")
    
    # Create trainer with in-memory database
    trainer = CalibrationTrainer(db_path=":memory:")
    collector = FeedbackCollector(trainer)
    
    # Simulate compliance findings with various confidence levels
    synthetic_findings = [
        # High confidence findings
        {"id": "finding_1", "confidence": 0.95, "issue_title": "Missing treatment frequency", "discipline": "pt"},
        {"id": "finding_2", "confidence": 0.92, "issue_title": "Goals not updated", "discipline": "pt"},
        {"id": "finding_3", "confidence": 0.88, "issue_title": "Medical necessity unclear", "discipline": "ot"},
        
        # Medium confidence findings
        {"id": "finding_4", "confidence": 0.75, "issue_title": "Progress documentation", "discipline": "pt"},
        {"id": "finding_5", "confidence": 0.68, "issue_title": "Assessment incomplete", "discipline": "slp"},
        {"id": "finding_6", "confidence": 0.72, "issue_title": "Discharge planning", "discipline": "ot"},
        
        # Lower confidence findings
        {"id": "finding_7", "confidence": 0.55, "issue_title": "Billing code accuracy", "discipline": "pt"},
        {"id": "finding_8", "confidence": 0.48, "issue_title": "Supervision documentation", "discipline": "slp"},
        {"id": "finding_9", "confidence": 0.52, "issue_title": "Equipment usage", "discipline": "ot"},
    ]
    
    # Simulate user feedback - higher confidence findings are more likely to be correct
    feedback_patterns = {
        0.9: 0.85,  # 90%+ confidence findings are correct 85% of the time
        0.8: 0.75,  # 80%+ confidence findings are correct 75% of the time
        0.7: 0.65,  # 70%+ confidence findings are correct 65% of the time
        0.6: 0.55,  # 60%+ confidence findings are correct 55% of the time
        0.5: 0.45,  # 50%+ confidence findings are correct 45% of the time
    }
    
    import random
    random.seed(42)  # For reproducible results
    
    feedback_count = {"correct": 0, "incorrect": 0}
    
    # Collect feedback for multiple rounds to get enough training data
    for round_num in range(8):  # 8 rounds × 9 findings = 72 samples
        print(f"   • Round {round_num + 1}: Collecting feedback on {len(synthetic_findings)} findings")
        
        for finding in synthetic_findings:
            confidence = finding["confidence"]
            
            # Determine if finding should be correct based on confidence
            correct_probability = 0.45  # Base rate
            for threshold, prob in feedback_patterns.items():
                if confidence >= threshold:
                    correct_probability = prob
                    break
            
            is_correct = random.random() < correct_probability
            feedback = "correct" if is_correct else "incorrect"
            
            # Add some variation to confidence (simulate real-world scenario)
            varied_confidence = confidence + random.uniform(-0.05, 0.05)
            varied_confidence = max(0.1, min(0.95, varied_confidence))
            
            finding_with_variation = finding.copy()
            finding_with_variation["confidence"] = varied_confidence
            finding_with_variation["original_confidence"] = varied_confidence
            
            collector.process_feedback(finding_with_variation, feedback, user_id=f"therapist_{round_num % 3 + 1}")
            feedback_count[feedback] += 1
    
    print(f"   • Collected {feedback_count['correct']} correct and {feedback_count['incorrect']} incorrect feedback samples")
    
    # Get feedback statistics
    stats = trainer.get_feedback_statistics()
    print(f"   • Total feedback samples: {stats['total_feedback']}")
    print(f"   • Feedback distribution: {stats['feedback_distribution']}")
    
    return trainer


async def demonstrate_ml_training_pipeline():
    """Demonstrate the complete ML training pipeline."""
    print("🤖 ML Training Pipeline Demo")
    print("=" * 50)
    
    # Step 1: Simulate feedback collection
    trainer = await simulate_user_feedback_collection()
    
    # Step 2: Create ML training pipeline
    print(f"\n🔧 Setting up ML training pipeline...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        pipeline = MLTrainingPipeline(
            calibration_trainer=trainer,
            models_dir=temp_dir
        )
        
        print(f"   • Models directory: {temp_dir}")
        print(f"   • Minimum samples for training: {pipeline.min_samples_for_training}")
        print(f"   • Performance threshold: {pipeline.performance_threshold}")
        
        # Step 3: Run training pipeline
        print(f"\n🚀 Running ML training pipeline...")
        
        start_time = datetime.now()
        result = await pipeline.fine_tune_model_with_feedback(force_retrain=True)
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"   • Training completed in {duration:.2f} seconds")
        print(f"   • Status: {result['status']}")
        
        # Step 4: Display results
        if result['status'] == 'completed':
            print(f"\n📊 Training Results:")
            
            training_results = result['training_results']
            print(f"   • Calibration method used: {training_results['method_used']}")
            print(f"   • Training samples: {training_results['samples_used']}")
            
            eval_results = result['evaluation_results']
            print(f"   • Raw ECE: {eval_results['raw_ece']:.4f}")
            print(f"   • Calibrated ECE: {eval_results['calibrated_ece']:.4f}")
            print(f"   • ECE improvement: {eval_results['ece_improvement']:.1%}")
            print(f"   • Brier improvement: {eval_results['brier_improvement']:.1%}")
            
            deployment_results = result['deployment_results']
            print(f"   • Model deployed: {deployment_results['deployed']}")
            if deployment_results['deployed']:
                print(f"   • Deployment reason: {deployment_results['reason']}")
            else:
                print(f"   • Not deployed: {deployment_results['reason']}")
        
        elif result['status'] == 'insufficient_data':
            print(f"   • Insufficient training data: {result['samples_collected']} samples")
            print(f"   • Need {pipeline.min_samples_for_training} samples for training")
        
        else:
            print(f"   • Training result: {result}")
        
        # Step 5: Demonstrate scheduler
        print(f"\n⏰ Demonstrating ML Scheduler...")
        
        scheduler = MLScheduler(training_pipeline=pipeline)
        
        # Get scheduler status
        status = scheduler.get_scheduler_status()
        print(f"   • Scheduler running: {status['is_running']}")
        
        # Show what would happen with scheduled training
        print(f"   • Would normally run training daily at 2:00 AM")
        print(f"   • Health checks would run every 6 hours")
        
        # Demonstrate health check
        health_status = await scheduler._check_system_health()
        print(f"   • System health: {health_status['overall_status']}")
        print(f"   • Training data count: {health_status['metrics'].get('training_data_count', 0)}")
        
        if health_status['warnings']:
            print(f"   • Warnings: {health_status['warnings']}")
        
        # Step 6: Show continuous improvement potential
        print(f"\n🔄 Continuous Improvement Cycle:")
        print(f"   1. Users provide feedback on AI findings")
        print(f"   2. Feedback is collected and stored in database")
        print(f"   3. ML pipeline automatically trains new calibrators")
        print(f"   4. Improved models are deployed if they meet quality thresholds")
        print(f"   5. Better confidence scores lead to more trustworthy AI")
        print(f"   6. Cycle repeats with new feedback")
        
        print(f"\n✅ ML Training Pipeline Demo Complete!")
        print(f"\n💡 Key Benefits:")
        print(f"   • Replaced placeholder with real implementation")
        print(f"   • Automatic model improvement from user feedback")
        print(f"   • Quality-gated deployment (only deploy if improved)")
        print(f"   • Scheduled training and health monitoring")
        print(f"   • Complete audit trail and metrics")


async def main():
    """Run the ML training pipeline demonstration."""
    try:
        await demonstrate_ml_training_pipeline()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())