#!/usr/bin/python

from distutils.core import setup
import os

def is_package(path):
    return (
        os.path.isdir(path) and
        os.path.isfile(os.path.join(path, '__init__.py'))
        )

def find_packages(path, base="" ):
    """ Find all packages in path """
    packages = {}
    for item in os.listdir(path):
        dir = os.path.join(path, item)
        if is_package( dir ):
            if base:
                module_name = "%(base)s.%(item)s" % vars()
            else:
                module_name = item
            packages[module_name] = dir
            packages.update(find_packages(dir, module_name))
    return packages

packages = find_packages(".")
package_names = packages.keys()

setup(name = "python-guild",
      version = "1.0.0",
      description = "python-guild",
     
      author = "Michael Sparks",
      author_email = "sparks.m@gmail.com",
      url = "http://sparkslabs.com/michael/",
      license ="Apache Software License",
      packages = package_names,
      package_dir = packages,
#      scripts = [
#                  'scripts/guildservice',
#                ],
#      data_files=[
#                   ('/etc/init',         ['etc/init/guildservice.conf']),
#                   ('/etc/guildservice', ["etc/guildservice/config.json"])
#                 ],

      long_description = """
This is initially just a collection of random test ideas. It may grow into
something more interesting.  It may not.
""",
      )
