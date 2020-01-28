from setuptools import setup

setup(
    name='mkdocs-paywall',
    version='0.1.0',
    description='Dokknet Paywall Plugin for Mkdocs',
    author='Agost Biro',
    author_email='agost@dokknet.com',
    packages=['plugin'],
    entry_points={
        'mkdocs.plugins': [
            'mkdocs-paywall= plugin:PaywallPlugin',
        ]
    }
)
