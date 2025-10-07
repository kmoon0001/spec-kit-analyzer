"""
Tests for Report Generation Engine

This module tests the core reporting system to ensure it integrates properly
with existing systems without breaking functionality.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import yaml

from src.core.report_generation_engine import (
    Re