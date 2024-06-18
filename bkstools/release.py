# -*- coding: UTF-8 -*-
#######################################################################
#
## \file
#  \section bkstools_release_py_general General file information
#
#    \author   Dirk Osswald
#    \date     2018-11-19
#
#  \brief
#    Definition and documentation of the project name and the release
#    name ("version") of the package
#
#  \section bkstools_release_py_copyright Copyright
#
#  Copyright (c) 2018 SCHUNK GmbH & Co. KG
#
#  <HR>
#  \internal
#
#    \subsection bkstools_release_py_details SVN related, detailed file specific information:
#      $LastChangedBy: DirkOsswald $
#      $LastChangedDate: 2018-10-16 14:11:19 +0200 (Tue, 16 Oct 2018) $
#      \par SVN file revision:
#        $Id$
#
#  \subsection bkstools_release_py_changelog Changelog of this file:
#      \include release.py.log
#
#######################################################################

#######################################################################
## \anchor bkstools_release_py_python_vars
#  \name   Python specific variables
#
#  Some definitions that describe the module for python.
#
#  @{

__doc__       = """Definition and documentation of the project name and the release name ("version") for bkstools"""  # @ReservedAssignment
__author__    = "Dirk Osswald: dirk.osswald@de.schunk.com"
__url__       = "http://www.schunk.com"
__version__   = "$Id$"
__copyright__ = "Copyright (c) 2018 SCHUNK GmbH & Co. KG"

#  end of doxygen name group bkstools_release_py_python_vars
#  @}
######################################################################

######################################################################
# Define some variables

## \brief Name of the software "SCHUNK Python Modules" project.
#
#  \anchor project_name_bkstools
#  The name of the project
#
#    \internal
#    \remark
#    - This name is extracted by the makefile and then used by doxygen:
#      - As name of the project within the generated documentation.
#      - As base name of the generated install directory and pdf files.
#    - The name should \b NOT contain spaces!
#
PROJECT_NAME = "bkstools"

## \brief Release name of the whole software project (a.k.a. as the \e "version" of the project).
#
#    \anchor project_release_bkstools
#    The release name of the project.
#
#    A suffix of "-dev" indicates a work in progress, i.e. a not yet finished release.
#    A suffix of "-a", "-b", ... indicates a bugfix release.
#
#    From newest to oldest the releases have the following names and features:
#
#    - \b 0.0.2.27 2024-06-18
#      - No functional change. Added stuff for publishing via pip.

#    - \b 0.0.2.26 2024-01-08
#      - No functional change. Removed hints to future gripper type from descriptions.
#
#    - \b 0.0.2.25 2023-12-19
#      - integrated stripped down pyschunk for easy publication
#      - Public release on GitHub
#
#    - \b 0.0.2.24 2023-12-08
#      - corrected support for Modbus-RTU on Linux
#
#    ...internal versions...
#
#    - \b 0.0.0.1: 2018-11-30
#      - Initial internal "release" of the code
#      - Scripts egi, egi_move and egi_ref are working
#
PROJECT_RELEASE = "0.0.2.27"

## \brief Date of the release of the software project.
#
#    \anchor project_date_bkstools
#    The date of the release of the project.
#
PROJECT_DATE = "2024-06-18"
