"""
Pytest configuration and fixtures for MARRVEL-MCP tests.

This module provides:
- SSL certificate verification check for integration tests
- Custom pytest markers
- Shared fixtures
"""

import pytest
import ssl
import certifi
import httpx


def check_ssl_configuration() -> bool:
    """
    Check if SSL certificates are properly configured.

    Attempts to verify SSL configuration by creating an SSL context
    and checking if certifi's CA bundle is accessible.

    Returns:
        bool: True if SSL is properly configured, False otherwise
    """
    try:
        # Check if certifi can locate the CA bundle
        ca_bundle = certifi.where()
        if not ca_bundle:
            return False

        # Try to create an SSL context
        ssl_context = ssl.create_default_context(cafile=ca_bundle)
        return True
    except (ssl.SSLError, OSError, Exception):
        return False


def check_network_connectivity() -> bool:
    """
    Check if network connectivity to MARRVEL API is available.

    Returns:
        bool: True if network is accessible, False otherwise
    """
    try:
        # Simple check - just attempt to resolve the domain
        import socket

        socket.gethostbyname("marrvel.org")
        return True
    except (socket.gaierror, OSError):
        return False


# Marker for skipping tests when SSL is not properly configured
skip_if_ssl_broken = pytest.mark.skipif(
    not check_ssl_configuration(),
    reason="SSL certificates not properly configured. "
    "Run: pip install --upgrade certifi",
)

# Marker for skipping tests when network is unavailable
skip_if_no_network = pytest.mark.skipif(
    not check_network_connectivity(),
    reason="Network connectivity to MARRVEL API unavailable",
)
