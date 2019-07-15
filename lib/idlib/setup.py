import setuptools

with open("README.md", 'r') as inF:
    long_description = inF.read()

setuptools.setup(
    name="idlib",
    version="0.0.1",
    author="Jake Vasilakes",
    author_email="vasil024@umn.edu",
    description="The iDISK API.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ],
)
