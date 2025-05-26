from setuptools import setup, find_packages

setup(
    name="hudi_data_pipeline",
    version="0.1.0",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "dagster",
        "dagster-postgres",
        "dagster-docker",
        "dagster-k8s",
        "pyspark==3.5.5",
        "PyYAML>=6.0",
        "pandas>=1.3.0",
        "python-dotenv",
        "dagster-aws",
        "dagster-webserver"
    ],
    extras_require={
        "dev": [
            "pytest",
            "black",
            "isort",
            "mypy",
            "pytest-cov",
        ],
    },
    author="Duc Nguyen",
    author_email="nguyenhuynhduc.991999@gmail.com",
    description="Dagster pipeline for Hudi-based incremental data processing",
)