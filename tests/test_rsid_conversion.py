"""
Tests for convert_rsid_to_variant (issue #338).

dbSNP reports allele positions as 0-based SPDI; MARRVEL/VCF coordinates are
1-based. These tests pin the conversion, multiallelic handling, indel anchoring
and the Clinical Tables fallback using mocked HTTP responses, plus a live
round-trip check against NCBI marked as an integration test.
"""

import json

import httpx
import pytest

from marrvel_mcp import server

GRCH38_TRAITS = [{"assembly_name": "GRCh38.p14", "is_top_level": True, "is_chromosome": True}]
GRCH37_TRAITS = [{"assembly_name": "GRCh37.p13", "is_top_level": True, "is_chromosome": True}]


def _allele(seq_id, position, deleted, inserted, hgvs):
    return {
        "allele": {
            "spdi": {
                "seq_id": seq_id,
                "position": position,
                "deleted_sequence": deleted,
                "inserted_sequence": inserted,
            }
        },
        "hgvs": hgvs,
    }


def _refsnp(alleles38, genes=("MYH7",), seq_id="NC_000014.9", grch37_first=True):
    placements = [
        {
            "seq_id": seq_id,
            "is_ptlp": True,
            "placement_annot": {"seq_id_traits_by_assembly": GRCH38_TRAITS},
            "alleles": alleles38,
        }
    ]
    if grch37_first:
        # A GRCh37 placement listed first must be ignored.
        placements.insert(
            0,
            {
                "seq_id": "NC_000014.8",
                "is_ptlp": False,
                "placement_annot": {"seq_id_traits_by_assembly": GRCH37_TRAITS},
                "alleles": [_allele("NC_000014.8", 23898486, "C", "T", "x")],
            },
        )
    return {
        "refsnp_id": "1",
        "primary_snapshot_data": {
            "placements_with_allele": placements,
            "allele_annotations": [
                {"assembly_annotation": [{"genes": [{"locus": g} for g in genes]}]}
            ],
        },
    }


# rs121913624 (MYH7 p.R403Q): SPDI position 23429277 == HGVS g.23429278
RS121913624 = _refsnp(
    [
        _allele("NC_000014.9", 23429277, "C", "C", "NC_000014.9:g.23429278="),
        _allele("NC_000014.9", 23429277, "C", "A", "NC_000014.9:g.23429278C>A"),
        _allele("NC_000014.9", 23429277, "C", "G", "NC_000014.9:g.23429278C>G"),
        _allele("NC_000014.9", 23429277, "C", "T", "NC_000014.9:g.23429278C>T"),
    ]
)

RS_SINGLE = _refsnp(
    [
        _allele("NC_000007.14", 117587805, "G", "G", "NC_000007.14:g.117587806="),
        _allele("NC_000007.14", 117587805, "G", "A", "NC_000007.14:g.117587806G>A"),
    ],
    genes=("CFTR",),
    seq_id="NC_000007.14",
    grch37_first=False,
)

# rs113993960 (CFTR F508del): indel needs NCBI's vcf_fields for the anchor base
RS_INDEL = _refsnp(
    [
        _allele("NC_000007.14", 117559590, "TCTT", "TCTT", "NC_000007.14:g.117559591_117559594="),
        _allele("NC_000007.14", 117559590, "TCTT", "T", "NC_000007.14:g.117559592_117559594del"),
    ],
    genes=("CFTR",),
    seq_id="NC_000007.14",
    grch37_first=False,
)


@pytest.fixture
def mock_http(monkeypatch):
    """Route create_http_client() through an httpx.MockTransport; returns the request log."""
    routes = {}
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        key = request.url.path if "ncbi" in request.url.host else request.url.host
        if key not in routes:
            return httpx.Response(404, json={"error": {"code": 404}})
        status, body = routes[key]
        return httpx.Response(status, json=body)

    monkeypatch.setattr(
        server,
        "create_http_client",
        lambda *a, **k: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    monkeypatch.setattr(server, "NCBI_VARIATION_MIN_INTERVAL", 0)
    return routes, requests


async def _convert(rsid):
    return json.loads(await server.convert_rsid_to_variant(rsid))


def test_refseq_chromosome_name():
    assert server._refseq_chromosome_name("NC_000007.14") == "7"
    assert server._refseq_chromosome_name("NC_000023.11") == "X"
    assert server._refseq_chromosome_name("NC_000024.10") == "Y"
    assert server._refseq_chromosome_name("NC_012920.1") == "MT"
    assert server._refseq_chromosome_name("NG_016465.4") is None


@pytest.mark.asyncio
async def test_multiallelic_returns_all_alts_at_1_based_position(mock_http):
    routes, _ = mock_http
    routes["/variation/v0/refsnp/121913624"] = (200, RS121913624)

    out = await _convert("rs121913624")

    assert out["multiallelic"] is True
    assert out["chr"] == "14"
    assert out["alleles"] == "C/A, C/G, C/T"
    assert [v["variant"] for v in out["variants"]] == [
        "14-23429278-C-A",
        "14-23429278-C-G",
        "14-23429278-C-T",
    ]
    # No single allele is presented as "the" variant for a multiallelic rsID.
    assert "variant" not in out and "alt" not in out
    assert "note" in out
    # The pathogenic R403Q allele is available and matches its HGVS.
    r403q = next(v for v in out["variants"] if v["alt"] == "T")
    assert r403q["hgvs_g"] == "NC_000014.9:g.23429278C>T"
    assert out["gene"] == "MYH7"


@pytest.mark.asyncio
async def test_single_alt_keeps_top_level_fields(mock_http):
    routes, _ = mock_http
    routes["/variation/v0/refsnp/75527207"] = (200, RS_SINGLE)

    out = await _convert("75527207")

    assert out["multiallelic"] is False
    assert out["variant"] == "7-117587806-G-A"
    assert (out["pos"], out["ref"], out["alt"]) == (117587806, "G", "A")
    assert out["hgvs_g"] == "NC_000007.14:g.117587806G>A"


@pytest.mark.asyncio
async def test_indel_uses_ncbi_vcf_fields_for_anchor_base(mock_http):
    routes, requests = mock_http
    routes["/variation/v0/refsnp/113993960"] = (200, RS_INDEL)
    routes["/variation/v0/spdi/NC_000007.14:117559590:TCTT:T/vcf_fields"] = (
        200,
        {"data": {"chrom": "NC_000007.14", "pos": 117559590, "ref": "ATCT", "alt": "A"}},
    )

    out = await _convert("rs113993960")

    assert out["variant"] == "7-117559590-ATCT-A"
    assert any(r.url.path.endswith("/vcf_fields") for r in requests)


@pytest.mark.asyncio
async def test_merged_rsid_is_followed(mock_http):
    routes, _ = mock_http
    routes["/variation/v0/refsnp/999"] = (
        200,
        {"refsnp_id": "999", "merged_snapshot_data": {"merged_into": ["75527207"]}},
    )
    routes["/variation/v0/refsnp/75527207"] = (200, RS_SINGLE)

    out = await _convert("rs999")

    assert out["merged_into"] == "rs75527207"
    assert out["variant"] == "7-117587806-G-A"


@pytest.mark.asyncio
async def test_unknown_rsid_returns_error_without_fallback(mock_http):
    _, requests = mock_http

    out = await _convert("rs2")

    assert "not found" in out["error"]
    assert all("ncbi" in r.url.host for r in requests)


@pytest.mark.asyncio
async def test_invalid_rsid():
    out = await _convert("rsABC")
    assert "Invalid rsID" in out["error"]


@pytest.mark.asyncio
async def test_fallback_to_clinical_tables_adds_one_and_skips_indels(mock_http):
    routes, _ = mock_http
    routes["/variation/v0/refsnp/121913624"] = (500, {"error": "boom"})
    routes["clinicaltables.nlm.nih.gov"] = (
        200,
        [
            1,
            ["rs121913624"],
            {
                "38.chr": ["14"],
                "38.pos": ["23429277"],
                "38.alleles": ["C/A, C/T, C/CT"],
                "38.gene": ["MYH7"],
            },
        ],
    )

    out = await _convert("rs121913624")

    assert [v["variant"] for v in out["variants"]] == ["14-23429278-C-A", "14-23429278-C-T"]
    assert out["skipped_indel_alleles"] == ["C/CT"]
    assert "fallback" in out["source"]
    assert "warning" in out


# Live round trip against NCBI: positions must equal the 1-based HGVS/protein
# conversion coordinates reported in issue #338, and the intended allele must
# be among the returned alternates.
ROUND_TRIP = [
    ("rs121913624", "14-23429278-C-T"),  # MYH7 p.R403Q
    ("rs3218713", "14-23431468-C-T"),  # MYH7 p.R249Q
    ("rs121913637", "14-23425971-G-A"),  # MYH7 p.R719W
    ("rs121913626", "14-23427723-C-G"),  # MYH7 p.G584R
    ("rs75527207", "7-117587806-G-A"),  # CFTR p.G551D
]


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("rsid,expected", ROUND_TRIP)
async def test_live_round_trip(rsid, expected):
    out = await _convert(rsid)
    assert "error" not in out, out
    assert out["source"] == "NCBI dbSNP Variation Services"
    assert expected in [v["variant"] for v in out["variants"]]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_rs75527207_includes_g551v_allele():
    out = await _convert("rs75527207")
    assert {"7-117587806-G-A", "7-117587806-G-T"} <= {v["variant"] for v in out["variants"]}
