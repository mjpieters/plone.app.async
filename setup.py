from setuptools import setup, find_packages
import os

name = 'plone.app.async'
version = '1.0a4'
user_doc = open(
    os.path.join("src", "plone", "app", "async", "README.txt")).read()

setup(name=name,
      version=version,
      description="Integration package for zc.async",
      long_description=open("README.txt").read() + "\n" +
                       user_doc + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          'Environment :: Web Environment',
          'Framework :: Plone',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries :: Python Modules',
        ],
      keywords='plone, async, asynchronous',
      author='Plone Foundation',
      author_email='plone-developers@lists.sourceforge.net',
      url='http://plone.org/products/plone.app.async',
      download_url = 'http://pypi.python.org/pypi/plone.app.async/',
      license='GPL version 2',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['plone', 'plone.app'],
      include_package_data=True,
      platforms = 'Any',
      zip_safe=False,
      install_requires=[
          'setuptools',
          'zc.async',
          'zc.monitor',
          'zc.z3monitor',
          'collective.testcaselayer'
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
