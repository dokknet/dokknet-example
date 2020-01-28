#!/usr/bin/env python3
"""Build static site."""
import argparse
import subprocess


def build(site_dir):
    subprocess.run(['pip', 'install', './paywall_plugin'], check=True)
    subprocess.run(['mkdocs', 'build', '-d', site_dir], check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-d', '--site_dir', type=str,
                        default='./site',
                        help='Directory to build the site to')
    args = parser.parse_args()
    build(args.site_dir)
