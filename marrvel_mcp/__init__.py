"""
MARRVEL-MCP: Model Context Protocol server for MARRVEL genetics research platform.

This package provides AI agents access to comprehensive genetics databases including:
- Gene information (NCBI, RefSeq)
- Variant annotations (dbNSFP, ClinVar, gnomAD)
- Disease associations (OMIM)
- Ortholog predictions (DIOPT)
- Expression data (GTEx)
"""

__version__ = "1.0.0"
__author__ = "MARRVEL Team"

from .client import fetch_marrvel_data
from .server import create_server

__all__ = [
    "fetch_marrvel_data",
    "create_server",
]
