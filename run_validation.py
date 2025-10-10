#!/usr/bin/env python3
"""
Run system validation to check all components.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

async def run_validation():
    try:
        from src.core.system_validator import system_validator
        print('🚀 Running comprehensive system validation...')
        results = await system_validator.run_full_validation()
        report = system_validator.generate_validation_report(results)
        
        print('\n📊 Validation Results:')
        print(f'Overall Status: {report["overall_status"].upper()}')
        print(f'Total Tests: {report["total_tests"]}')
        print(f'Duration: {report["total_duration_ms"]:.1f}ms')
        print('\nStatus Breakdown:')
        for status, count in report["status_counts"].items():
            if count > 0:
                print(f'  {status}: {count}')
        
        print('\n🔍 Component Results:')
        for component, data in report["components"].items():
            print(f'  {component}: {data["status"]} ({data["test_count"]} tests)')
        
        print('\n💡 Recommendations:')
        for rec in report["recommendations"]:
            print(f'  • {rec}')
            
        return report["overall_status"] in ['pass', 'warning']
        
    except Exception as e:
        print(f'❌ Validation failed: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_validation())
    sys.exit(0 if success else 1)