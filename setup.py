from setuptools import setup

setup(
    name="blooket-helper",
    version="1.0.0",
    description="Human-like Playwright CDP automation for Blooket Study mode",
    py_modules=["script"],
    python_requires=">=3.10",
    install_requires=[
        "playwright>=1.40.0",
    ],
    entry_points={
        "console_scripts": [
            "blooket-bot=script:cli_entry",
        ],
    },
)