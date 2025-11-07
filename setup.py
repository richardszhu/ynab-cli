from setuptools import find_packages, setup

setup(
    name="ynab-cli",
    version="1.0.0",
    description="Misc. automations for YNAB",
    author="@richardszhu",
    py_modules=["ynab_cli"],
    entry_points={
        "console_scripts": [
            "ynab-cli=ynab_cli:cli",
        ],
    },
    install_requires=[
        "click>=8.0.0",
        "requests>=2.25.0",
        "python-dateutil>=2.8.0",
    ],
    python_requires=">=3.9",
)
