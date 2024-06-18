#!/usr/bin/env python setup.py
# -*- coding: UTF-8 -*-
#######################################################################
## \file
#  \section bkstools_setup_py_general General file information
#
#    \author   Dirk Osswald
#    \date     2018-11-28
#  \brief
#    Python setuptools setup script for bkstools package
#
#  \section bkstools_setup_py_copyright Copyright
#
#  - Copyright (c) 2018 SCHUNK GmbH & Co. KG
#
#  <HR>
#  \internal
#
#    \subsection bkstools_setup_py_details SVN related, detailed file specific information:
#      $LastChangedBy: Osswald2 $
#      $LastChangedDate: 2016-04-19 10:25:09 +0200 (Tue, 19 Apr 2016) $
#      \par SVN file revision:
#        $Id$
#
#  \subsection bkstools_setup_py_changelog Changelog of this file:
#      \include setup.py.log
#
#######################################################################

# Always prefer setuptools over distutils
from setuptools import setup, find_packages  # @UnusedImport
# To use a consistent encoding
from codecs import open
from os import path
try:
    import py2exe                                # @UnusedImport
except ImportError:
    pass
import sys

#---------------------
here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


#---------------------
# When generating standalone executables:
# - The windows icon must be available:
script_icon = path.join( ".", "schunk.ico")
#---

# - The MS dlls must be made available to avoid "error: [Errno 2] No such file or directory: 'MSVCP90.dll'":
ms_vc90_path = path.join( '.', 'Microsoft.VC90.CRT' )
sys.path.append( ms_vc90_path )
#---

# - Add the actual package dir to the path, so that release.py and the like are included by py2exe
from bkstools.release import PROJECT_DATE, PROJECT_NAME, PROJECT_RELEASE  # @UnresolvedImport @UnusedImport
#---

#---------------------
# the actual setup command that generates the distribution
try:
    setup (
        name =
            PROJECT_NAME,  # @UndefinedVariable

        # Versions should comply with PEP440.  For a discussion on single-sourcing
        # the version across setup.py and the project code, see
        # https://packaging.python.org/en/latest/single_source_version.html
        version =
            PROJECT_RELEASE,  # @UndefinedVariable

        description =
            PROJECT_NAME + ': Tools to interact with SCHUNK BKS grippers via the HTTP/JSON webinterface or Modbus-RTU',
        long_description =
            long_description,
        long_description_content_type =
            'text/markdown',

        # The project's main homepage.
        url =
            'https://github.com/SCHUNK-SE-Co-KG/bkstools.git',

        download_url = f'https://github.com/SCHUNK-SE-Co-KG/bkstools/archive/refs/tags/{PROJECT_RELEASE}_{PROJECT_DATE}.tar.gz',

        # Author details
        author =
            'Dirk Osswald',
        author_email =
            'dirk.osswald@de.schunk.com',

        # Choose your license
        license =
            'GPL v3',

        # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
        classifiers = [
            # How mature is this project? Common values are
            #   3 - Alpha
            #   4 - Beta
            #   5 - Production/Stable
            'Development Status :: 4 - Beta',

            # Indicate who your project is intended for
            'Intended Audience :: End Users/Desktop',
            'Topic :: Scientific/Engineering :: Human Machine Interfaces',

            # Pick your license as you wish (should match "license" above)
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

            # Specify the Python versions you support here. In particular, ensure
            # that you indicate whether you support Python 2, Python 3 or both.
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.10',
        ],

        # What does your project relate to?
        keywords =
            'SCHUNK gripper BKS EGI EGU EGK',

        packages = [
            "bkstools",
            "bkstools.bks_lib",
            "bkstools.scripts",
            "bkstools.demo",

            "pyschunk",
            "pyschunk.generated",
            "pyschunk.guistuff",
            "pyschunk.tools",
        ],

        # List run-time dependencies here.  These will be installed by pip when
        # your project is installed. For an analysis of "install_requires" vs pip's
        # requirements files see:
        # https://packaging.python.org/en/latest/requirements.html
        install_requires = [
            'requests>=2.26.0',
            'PyYAML>=5.4.1',
            'minimalmodbus>=2.0.1',
            'wrapt',

            # On Windows only:
            'pypiwin32 ; platform_system=="Windows"',
        ],

        python_requires='>=3',

        # If there are data files included in your packages that need to be
        # installed, specify them here.  If using Python 2.6 or less, then these
        # have to be included in MANIFEST.in as well.
        # \remark The package_date seems to be ignored for py2exe targets
        #         and is thus relevant for the bdist_* and sdist_* targets only
        package_data = {
            'pyschunk.guistuff': [     # from this package (use '' for any package)
                'pic/*.gif',           # use files matching these patterns
                'pic/*.ico',
                'pic/*.xbm',
            ],
        },

        # If set to True, this tells setuptools to automatically include any
        # data files it finds inside your package directories that are
        # specified by your MANIFEST.in file.
        # \remark If True then the package_data set above seems to be ignored!
#         include_package_data =
#             True,

        # Although 'package_data' is the preferred approach, in some case you may
        # need to place data files outside of your packages. See:
        # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
        # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
#         data_files=[('my_data', ['data/data_file'])],
        # \remark The data_files seems to be ignored for bdist_* and sdist_*
        #         targets and is thus relevant for the py2exe target only
#         data_files = [
#             ('my_data', [              # install into '<sys.prefix>/my_data'
#                 'data/data_file',      # from this 'data_file'
#                 ]
#             ),
#         ],
        data_files = [
            ( '.',  [ # target dir
                    'cmd-here.lnk',
                ]
            ),
            ( 'bkstools_data', [     # target dir
                        'bkstools/bkstools_data/default_settings.bak',
                        'bkstools/bkstools_data/default_settings.dat',
                        'bkstools/bkstools_data/default_settings.dir',
                      ]
            ),
        ],

        # To provide executable scripts, use entry points in preference to the
        # "scripts" keyword. Entry points provide cross-platform support and allow
        # pip to create the appropriate form of executable for the target platform.
        #
        # Remarks:
        #   - When installing the resulting wheel with pip on Linux as a
        #     non-root user then the scripts below will be installed e.g.
        #     in $HOME/.local/bin So to make them available that dir must be in your PATH.
        #   - When installing the resulting wheel with pip on Linux as
        #     root (e.g. with sudo) then the scripts below will be installed
        #     e.g. in /usr/local/bin which usually already is in PATH.
        #   - When installing the resulting wheel with pip on Windows as a
        #     non-Administrator then the scripts below willbe installed e.g.
        #     in %APPDATA%\Python\Python37\Scripts So to make them availabe
        #     that dir must be in your PATH.
        #   - When installing the resulting wheel with pip on Windows as
        #     Administrator then the scripts below willbe installed e.g.
        #     in c:\Program Files (x86)\Python37.32\Scripts\
        #     So to make them availabe that dir must be in your PATH (which
        #     it usually is if you told so on Python installation)
        entry_points = {
            'console_scripts': [
                'bks=bkstools.scripts.bks:main',
                'bks_move=bkstools.scripts.bks_move:main',
                'bks_grip=bkstools.scripts.bks_grip:main',
                'bks_jog=bkstools.scripts.bks_jog:main',
                'bks_status=bkstools.scripts.bks_status:main',
                'bks_scan=bkstools.scripts.bks_scan:main',
                'bks_get_system_messages=bkstools.scripts.bks_get_system_messages:main',
                'demo_simple=bkstools.demo.demo_simple:main',
                'demo_bks_grip_outside_inside=bkstools.demo.demo_bks_grip_outside_inside:main',
                'demo_grip_workpiece_with_expected_position=bkstools.demo.demo_grip_workpiece_with_expected_position:main',
                'demo_read_exception_status=bkstools.demo.demo_read_exception_status:main',
                'demo_diagnostics=bkstools.demo.demo_diagnostics:main',
            ],
#            #'gui_scripts': [
#            #    'runme=PC.runme:main',
#            #],
        },

#        scripts = [
#        #    'postinstall_bkstools.py',
#        ],

        options = {
            # When creating a standalone exe package with py2exe then some more settings are
            # required. These can be provided here:
            # (See also http://www.py2exe.org/index.cgi/ListOfOptions )
            'py2exe': {
                'unbuffered':          # True: enable unbuffered output
                    True,              #   required to make output appear immediately, e.g. after CTRL-I in COT_ReferenceTool
                'dist_dir':            # Directory where to generate the distribution
                    'build/%s-%s-py2exe' % (PROJECT_NAME, PROJECT_RELEASE),  # @UndefinedVariable
                'packages':            # List of packages to include with subpackages. Can be a list of packages as comma separated string like "packa, packb, packc"
                    'pkg_resources',   #   required to avoid error "ImportError: The 'packaging' package is required" from the generated exe
#                 'includes': [          # List of module names to include
#                     'six',
#                 ],
                'excludes': [          # List of module names to exclude
                    'pydevd', '_pydev_imps',  # including the (automatically found) pydevd stuff leads to errors when processing with py2exe
                    #'pkg_resources._vendor.packaging', # required to avoid error "TypeError: pkg_resources._vendor.packaging is not a package" on building the exe
                ],
#                 'bundle_files':        # 3 = don't bundle (default) 2 = bundle everything but the Python interpreter 1 = bundle everything, including the Python interpreter
#                                        #   \remark: - 1 : does not work (yields segfault or other errors when the generated executable is run (last tested 2016-08-19 with distutils/setuptools and py2exe (0.6.9)).
#                                        #            - 2 : does not work (yields segfault or other errors when the generated executable is run (last tested 2016-08-19 with distutils/setuptools and py2exe (0.6.9)).
#                     3,
#                 'optimize':            # string or int of optimization level (0, 1, or 2) 0 = don't optimize (generate .pyc) 1 = normal optimization (like python -O) 2 = extra optimization (like python -OO)
#                     0,
#                 'ascii' :                # Do not automatically include encodings and codecs
#                     False,
            },
        },

        # Py2exe extension to the Distutils/setuptools setup keywords:
        # (See also http://www.py2exe.org/index.cgi/ListOfOptions )
        console = [
            {
                'script':         cs, ### Main Python script
                'icon_resources': [(0, script_icon)]     ### Icon to embed into the PE file.
            }
            # For whatever reason the icon_resources option does not work for the first element in the
            # console_scripts list. Workaround: just duplicate that first entry...:
            for cs in [
                r'.\bkstools\scripts\bks.py',
                r'.\bkstools\scripts\bks.py',
                r'.\bkstools\scripts\bks_move.py',
                r'.\bkstools\scripts\bks_grip.py',
                r'.\bkstools\scripts\bks_jog.py',
                r'.\bkstools\scripts\bks_status.py',
                r'.\bkstools\scripts\bks_scan.py',
                r'.\bkstools\scripts\bks_get_system_messages.py',
                r'.\bkstools\demo\demo_simple.py',
                r'.\bkstools\demo\demo_bks_grip_outside_inside.py',
                r'.\bkstools\demo\demo_grip_workpiece_with_expected_position.py',
                r'.\bkstools\demo\demo_read_exception_status.py',
                r'.\bkstools\demo\demo_diagnostics.py',
            ]
        ],

    ) # end of setup() call

except RuntimeError as e:
    import traceback
    traceback.print_exc()

    print("\nIf the above error indicates an 'access denied' kind of error, then")
    print("This might be due to anti-virus software.")
    print("As a workaround disable anti-virus temporarily. ")
    print("(running with elevated UAC rights does not seem to help")
    input( "press return to give up" )
    sys.exit(1) # exit with error to stop makefile

######################################################################
# some usefull editing settings for emacs:
#
#;;; Local Variables: ***
#;;; mode:python ***
#;;; End: ***
#
######################################################################
