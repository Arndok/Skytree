from setuptools import setup, find_packages

setup(
    name="skytree",
    version="0.2.0",
    description="A 2D game framework for Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Pablo Reyes de Rojas",
    author_email="cushinho@gmail.com",
    url="https://github.com/Arndok/Skytree",
    license="CC BY-NC-SA 4.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "pygame==2.6",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.11",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
        "Topic :: Games/Entertainment"
    ],
    python_requires=">=3.6, <3.12"
)
