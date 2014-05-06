from distutils.core import setup
from glob import glob
import os


setup( name='VSS',
       version= '1.0',
       description='private package',
       py_package=['VSS'],
       provides=['VSS'],
       author='Ethan Furman',
       author_email='ethan@stoneleaf.us',
       classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'Programming Language :: Python',
     )

