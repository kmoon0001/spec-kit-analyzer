#!/usr/bin/env python3
"""
Log Analyzer for Therapy Compliance Analyzer
Analyzes application logs to identify issues and patterns.
"""

import re
from pathlib import Path
from collections import defaultdict


class LogAnalyzer:
    """Analyzes application logs for debugging."""

    def __init__(self):
        self.log_files = ["debug.log", "monitor.log", "temp_api_out.log", "temp_api_err.log"]
        self.issues = defaultdict(list)
        self.patterns = defaultdict(int)

    def analyze_file(self, file_path):
        """Analyze a single log file."""
        if not Path(file_path).exists():
            return

        print(f"📄 Analyzing {file_path}...")

        with open(file_path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            self._analyze_line(line.strip(), file_path, line_num)

    def _analyze_line(self, line, file_path, line_num):
        """Analyze a single log line."""
        if not line:
            return

        # Error patterns
        error_patterns = [
            (r"ERROR:", "error"),
            (r"Exception:", "exception"),
            (r"Traceback:", "traceback"),
            (r"Failed:", "failure"),
            (r"TimeoutError:", "timeout"),
            (r"ConnectionError:", "connection"),
            (r"MemoryError:", "memory"),
            (r"ImportError:", "import"),
            (r"ModuleNotFoundError:", "module"),
            (r"AttributeError:", "attribute"),
            (r"KeyError:", "key"),
            (r"ValueError:", "value"),
            (r"TypeError:", "type"),
        ]

        for pattern, category in error_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                self.issues[category].append(
                    {"file": file_path, "line": line_num, "content": line, "timestamp": self._extract_timestamp(line)}
                )
                break

        # Performance patterns
        perf_patterns = [
            (r"(\d+\.?\d*)\s*seconds?", "duration"),
            (r"(\d+)\s*MB", "memory"),
            (r"(\d+)\s*GB", "memory_gb"),
            (r"CPU.*?(\d+\.?\d*)%", "cpu"),
            (r"RAM.*?(\d+\.?\d*)%", "ram"),
        ]

        for pattern, category in perf_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for match in matches:
                self.patterns[f"{category}_{match}"] += 1

    def _extract_timestamp(self, line):
        """Extract timestamp from log line."""
        timestamp_patterns = [
            r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})",
            r"(\d{2}:\d{2}:\d{2})",
        ]

        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        return None

    def generate_report(self):
        """Generate analysis report."""
        print("\n📊 LOG ANALYSIS REPORT")
        print("=" * 60)

        # Error summary
        print("\n🚨 ERROR SUMMARY")
        print("-" * 30)
        for category, errors in self.issues.items():
            print(f"{category.upper()}: {len(errors)} occurrences")

        # Top errors
        if self.issues:
            print("\n🔍 TOP ERRORS")
            print("-" * 20)
            for category, errors in sorted(self.issues.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
                print(f"{category}: {len(errors)} times")
                for error in errors[:3]:  # Show first 3 examples
                    print(f"  {error['file']}:{error['line']} - {error['content'][:80]}...")

        # Performance patterns
        print("\n⚡ PERFORMANCE PATTERNS")
        print("-" * 30)
        duration_patterns = {k: v for k, v in self.patterns.items() if k.startswith("duration_")}
        if duration_patterns:
            print("Duration patterns:")
            for pattern, count in sorted(duration_patterns.items(), key=lambda x: x[1], reverse=True)[:5]:
                duration = pattern.replace("duration_", "")
                print(f"  {duration}s: {count} occurrences")

        memory_patterns = {k: v for k, v in self.patterns.items() if k.startswith("memory_")}
        if memory_patterns:
            print("Memory patterns:")
            for pattern, count in sorted(memory_patterns.items(), key=lambda x: x[1], reverse=True)[:5]:
                memory = pattern.replace("memory_", "")
                print(f"  {memory}: {count} occurrences")

        # Recommendations
        print("\n💡 RECOMMENDATIONS")
        print("-" * 20)

        if "error" in self.issues:
            print("• Fix critical errors first")
        if "timeout" in self.issues:
            print("• Increase timeout values for slow operations")
        if "memory" in self.issues:
            print("• Monitor memory usage and optimize")
        if "connection" in self.issues:
            print("• Check network connectivity and API endpoints")

        if not self.issues:
            print("• No critical issues found - application appears stable")

    def run_analysis(self):
        """Run complete log analysis."""
        print("🔍 THERAPY COMPLIANCE ANALYZER - LOG ANALYSIS")
        print("=" * 60)

        for log_file in self.log_files:
            self.analyze_file(log_file)

        self.generate_report()


if __name__ == "__main__":
    analyzer = LogAnalyzer()
    analyzer.run_analysis()
