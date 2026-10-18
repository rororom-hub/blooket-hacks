from setuptools import setup

setup(
    name="blooket-helper",
    version="1.0.0",
    description="Human-like Playwright CDP automation for Blooket Study mode",
    py_modules=["cdp", "mine", "jev", "solver_bot"],
    python_requires=">=3.10",
    install_requires=[
        "playwright>=1.40.0",
        "typesafe-sdk>=0.7.5",
    ],
    entry_points={
        "console_scripts": [
            "blooket-bot=mine:cli_entry",
        ],
    },
)