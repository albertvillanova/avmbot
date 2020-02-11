from setuptools import setup, find_packages

setup(
    name='wikidatabot',
    version='0.0.1',
    description='Bot for Wikidata',
    author='Albert Villanova del Moral',
    packages=find_packages(),
    install_requires=[
        'pywikibot',
        # Scripts:
        'mwparserfromhell',  # Parse tamplates in Wikipedia Pages (transfer_infotable: extract_templates_and_params)
        'xlrd',  # Excel support
    ],
    extras_require={
        'dev': [
            'pytest',
        ]
    }
)
