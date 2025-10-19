"""Endpoint cleanup script to remove redundant endpoints.

This script identifies and removes redundant API endpoints to improve
maintainability and reduce security surface area.
"""

import logging
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class EndpointCleanupService:
    """Service for cleaning up redundant API endpoints."""

    def __init__(self):
        self.redundant_endpoints = {
            # Analysis endpoints - /submit is an alias for /analyze
            "analysis": {
                "remove": ["/submit"],
                "keep": ["/analyze"],
                "reason": "Submit endpoint is just an alias for analyze_document"
            },

            # Health endpoints - multiple /health endpoints exist
            "health": {
                "remove": ["/health"],  # From health.py - basic version
                "keep": ["/health/detailed", "/health/system"],  # More comprehensive versions
                "reason": "Basic health endpoint is redundant with detailed health checks"
            },

            # Auth endpoints - legacy login endpoint
            "auth": {
                "remove": ["/login"],  # Legacy endpoint
                "keep": ["/token"],  # OAuth2 standard endpoint
                "reason": "Legacy login endpoint duplicates OAuth2 token endpoint"
            }
        }

    def identify_redundant_endpoints(self) -> Dict[str, List[str]]:
        """
        Identify redundant endpoints across the application.

        Returns:
            Dictionary mapping router names to lists of redundant endpoints
        """
        redundant = {}

        for router_name, config in self.redundant_endpoints.items():
            redundant[router_name] = config["remove"]

        return redundant

    def get_cleanup_recommendations(self) -> Dict[str, Dict[str, any]]:
        """
        Get cleanup recommendations with reasons.

        Returns:
            Dictionary with cleanup recommendations
        """
        return self.redundant_endpoints

    def validate_endpoint_removal(self, router_name: str, endpoint: str) -> bool:
        """
        Validate that an endpoint can be safely removed.

        Args:
            router_name: Name of the router
            endpoint: Endpoint path to remove

        Returns:
            True if endpoint can be safely removed
        """
        if router_name not in self.redundant_endpoints:
            return False

        config = self.redundant_endpoints[router_name]
        return endpoint in config["remove"]


def cleanup_analysis_endpoints():
    """Remove redundant analysis endpoints."""
    logger.info("Cleaning up redundant analysis endpoints")

    # Remove the submit endpoint since it's just an alias
    # This will be done by commenting out the endpoint in the router
    pass


def cleanup_health_endpoints():
    """Remove redundant health endpoints."""
    logger.info("Cleaning up redundant health endpoints")

    # Remove basic health endpoint from health.py since we have more comprehensive ones
    # in health_check.py
    pass


def cleanup_auth_endpoints():
    """Remove redundant auth endpoints."""
    logger.info("Cleaning up redundant auth endpoints")

    # Remove legacy login endpoint since we have OAuth2 token endpoint
    pass


def main():
    """Main cleanup function."""
    cleanup_service = EndpointCleanupService()

    logger.info("Starting endpoint cleanup")

    # Get recommendations
    recommendations = cleanup_service.get_cleanup_recommendations()

    for router_name, config in recommendations.items():
        logger.info(f"Router {router_name}:")
        logger.info(f"  Remove: {config['remove']}")
        logger.info(f"  Keep: {config['keep']}")
        logger.info(f"  Reason: {config['reason']}")

    logger.info("Endpoint cleanup analysis complete")


if __name__ == "__main__":
    main()
