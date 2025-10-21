"""
Setup configuration for MARRVEL-MCP package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="marrvel-mcp",
    version="1.0.0",
    author="MARRVEL Team",
    author_email="",
    description="Model Context Protocol server for MARRVEL genetics research platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hyunhwan-bcm/MARRVEL_MCP",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "marrvel-mcp=marrvel_mcp.server:run_server",
        ],
    },
    include_package_data=True,
    keywords="genetics genomics bioinformatics mcp model-context-protocol marrvel",
)
