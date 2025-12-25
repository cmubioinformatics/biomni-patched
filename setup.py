from setuptools import setup, find_packages

setup(
    name="biomni-patched",
    version="0.1.0",
    description="Patched version of Biomni with custom fixes",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "openai",
        "anthropic",
        "pandas",
        "numpy",
        "requests",
    ],
)
