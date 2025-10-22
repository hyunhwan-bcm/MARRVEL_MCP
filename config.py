"""
Configuration file for MARRVEL-MCP server.

You can customize server settings here.
"""

# API Configuration
API_BASE_URL = "https://marrvel.org/data"
API_TIMEOUT = 30.0  # seconds
API_MAX_RETRIES = 3

# SSL Configuration
# Set to False to bypass SSL certificate verification (useful for development/testing)
# WARNING: Only disable for testing! Never use in production with sensitive data
VERIFY_SSL = False  # Set to True for production

# Server Configuration
SERVER_NAME = "MARRVEL"
SERVER_VERSION = "1.0.0"

# Logging Configuration
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Cache Configuration (if implemented)
ENABLE_CACHE = False
CACHE_TTL = 3600  # seconds (1 hour)
CACHE_MAX_SIZE = 1000  # maximum number of cached responses

# Rate Limiting (if implemented)
RATE_LIMIT_ENABLED = False
RATE_LIMIT_CALLS = 10  # requests per period
RATE_LIMIT_PERIOD = 1  # seconds

# Default Taxonomy IDs
TAXONOMY_IDS = {
    "human": "9606",
    "mouse": "10090",
    "rat": "10116",
    "zebrafish": "7955",
    "fly": "7227",
    "drosophila": "7227",
    "worm": "6239",
    "c_elegans": "6239",
    "yeast": "4932",
}

# Common gene symbols for testing
TEST_GENES = {"TP53": "7157", "BRCA1": "672", "BRCA2": "675", "CFTR": "1080", "APOE": "348"}

# Coordinate system
DEFAULT_GENOME_BUILD = "hg19"  # MARRVEL uses hg19/GRCh37
SUPPORTED_BUILDS = ["hg19", "GRCh37"]

# Tool categories for documentation
TOOL_CATEGORIES = {
    "gene": ["get_gene_by_entrez_id", "get_gene_by_symbol", "get_gene_by_position"],
    "variant": [
        "get_variant_dbnsfp",
        "get_clinvar_by_variant",
        "get_clinvar_by_gene_symbol",
        "get_clinvar_by_entrez_id",
        "get_gnomad_variant",
        "get_gnomad_by_gene_symbol",
        "get_gnomad_by_entrez_id",
        "get_dgv_variant",
        "get_dgv_by_entrez_id",
        "get_decipher_variant",
        "get_decipher_by_location",
        "get_geno2mp_variant",
        "get_geno2mp_by_entrez_id",
    ],
    "disease": ["get_omim_by_mim_number", "get_omim_by_gene_symbol", "get_omim_variant"],
    "ortholog": ["get_diopt_orthologs", "get_diopt_alignment"],
    "expression": ["get_gtex_expression", "get_ortholog_expression", "get_pharos_targets"],
    "utility": ["validate_hgvs_variant", "convert_protein_variant"],
}

# Error messages
ERROR_MESSAGES = {
    "gene_not_found": "Gene not found in MARRVEL database",
    "variant_not_found": "Variant not found in database",
    "invalid_format": "Invalid format. Please check your input",
    "invalid_chromosome": "Invalid chromosome. Use chr1-22, chrX, chrY, or chrM",
    "invalid_taxon": "Invalid taxonomy ID. See documentation for supported species",
    "api_timeout": "API request timed out. Please try again",
    "api_error": "Error communicating with MARRVEL API",
}
