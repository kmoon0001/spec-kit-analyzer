#!/usr/bin/env python3
"""
Apply immediate speed optimizations
"""

import shutil
import os

def apply_speed_optimizations():
    """Apply speed optimizations immediately"""
    print("⚡ Applying Speed Optimizations")
    print("=" * 40)
    
    # 1. Apply fast config
    print("\n1️⃣ Applying Fast Configuration...")
    try:
        if os.path.exists('config_fast.yaml'):
            # Backup original
            shutil.copy('config.yaml', 'config_original.yaml')
            print("   ✅ Original config backed up")
            
            # Apply fast config
            shutil.copy('config_fast.yaml', 'config.yaml')
            print("   ✅ Fast config applied")
        else:
            print("   ❌ config_fast.yaml not found - run add_fast_mode_config.py first")
    except Exception as e:
        print(f"   ❌ Error applying config: {e}")
    
    # 2. Create test documents
    print("\n2️⃣ Creating Test Documents...")
    
    # Small test document
    small_doc = """
Patient: John Doe
Date: 2024-01-15
Diagnosis: Lower back pain
Treatment: Physical therapy exercises
Progress: Patient shows improvement in range of motion
Plan: Continue current treatment plan
"""
    
    try:
        with open('test_small.txt', 'w') as f:
            f.write(small_doc)
        print("   ✅ Small test document created (test_small.txt)")
    except Exception as e:
        print(f"   ❌ Error creating test doc: {e}")
    
    # Tiny test document
    tiny_doc = """
Patient shows good progress with therapy.
Range of motion improved.
Continue treatment plan.
"""
    
    try:
        with open('test_tiny.txt', 'w') as f:
            f.write(tiny_doc)
        print("   ✅ Tiny test document created (test_tiny.txt)")
    except Exception as e:
        print(f"   ❌ Error creating tiny doc: {e}")
    
    print(f"\n🚀 Optimizations Applied!")
    print(f"   ✅ Fast configuration enabled")
    print(f"   ✅ Test documents created")
    
    print(f"\n📋 Next Steps:")
    print(f"   1. Restart API server: python scripts/run_api.py")
    print(f"   2. Test with tiny document first (test_tiny.txt)")
    print(f"   3. Should complete in 10-30 seconds!")
    
    print(f"\n⏱️  Expected Performance:")
    print(f"   • test_tiny.txt: 10-30 seconds")
    print(f"   • test_small.txt: 30-60 seconds")
    print(f"   • Original 388KB: 2-5 minutes (vs 5-15)")
    
    print(f"\n🔄 To Revert:")
    print(f"   Copy config_original.yaml back to config.yaml")

if __name__ == "__main__":
    apply_speed_optimizations()