import setuptools

with open("README", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='plint',
    version='0.1',
    author="Antoine Amarilli",
    author_email="a3nm@a3nm.net",
    description="French poetry validator",
    package_data={'plint' :['data/*', 'res/*']},
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/a3nm/plint",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    entry_points={
        'console_scripts': [
            'poemlint=plint.__main__:main',
        ],
    },
)
