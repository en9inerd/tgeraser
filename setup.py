"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
import pathlib
from setuptools import setup, find_packages


here = pathlib.Path(__file__).parent.resolve()
long_description = (here / 'README.md').read_text(encoding='utf-8')
PROJECT_NAME = 'tgeraser'
VERSION = '0.3.3'

setup(
    name=PROJECT_NAME,  # Required
    version=VERSION,  # Required
    description='Tool deletes all your messages from chat/channel/dialog on Telegram',  # Optional
    long_description=long_description,  # Optional
    long_description_content_type='text/markdown',  # Optional
    url='https://github.com/eng1nerd/' + PROJECT_NAME,  # Optional
    author='Vladimir Loskutov',  # Optional
    author_email='vladimir@enginerd.io',  # Optional
    classifiers=[  # Optional
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
    ],
    keywords='telegram, api, delete messages',  # Optional
    package_dir={},  # Optional
    packages=find_packages(exclude=["tests"]),  # Required
    python_requires='>=3.5, <4',
    install_requires=[  # Optional
        'docopt',
        'pyaes',
        'pyasn1',
        'pyyaml',
        'rsa',
        'telethon',
    ],
    extras_require={  # Optional
    },
    package_data={  # Optional
    },
    data_files=[],  # Optional
    entry_points={  # Optional
        'console_scripts': [
            'tgeraser=tgeraser.core:entry',
        ],
    },
    project_urls={  # Optional
    },
)
