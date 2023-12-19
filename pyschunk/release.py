# -*- coding: UTF-8 -*-
#######################################################################
#
## \file
#  \section pyschunk_release_py_general General file information
#
#    \author   Dirk Osswald
#    \date     2014-09-02
#
#  \brief
#    Definition and documentation of the project name and the release
#    name ("version") of the package
#
#  \section pyschunk_release_py_copyright Copyright
#
#  Copyright (c) 2014 SCHUNK GmbH & Co. KG
#
#  <HR>
#  \internal
#
#    \subsection pyschunk_release_py_details SVN related, detailed file specific information:
#      $LastChangedBy$
#      $LastChangedDate$
#      \par SVN file revision:
#        $Id$
#
#  \subsection pyschunk_release_py_changelog Changelog of this file:
#      \include release.py.log
#
#######################################################################

#######################################################################
## \anchor pyschunk_release_py_python_vars
#  \name   Python specific variables
#
#  Some definitions that describe the module for python.
#
#  @{

__doc__       = """Definition and documentation of the project name and the release name ("version") for pyschunk"""  # @ReservedAssignment
__author__    = "Dirk Osswald: dirk.osswald@de.schunk.com"
__url__       = "http://www.schunk.com"
__version__   = "$Id$"
__copyright__ = "Copyright (c) 2014 SCHUNK GmbH & Co. KG"

#  end of doxygen name group pyschunk_release_py_python_vars
#  @}
######################################################################

######################################################################
# Define some variables

## \brief Name of the software "SCHUNK Python Modules" project.
#
#  \anchor project_name_pyschunk
#  The name of the project
#
#    \internal
#    \remark
#    - This name is extracted by the makefile and then used by doxygen:
#      - As name of the project within the generated documentation.
#      - As base name of the generated install directory and pdf files.
#    - The name should \b NOT contain spaces!
#
PROJECT_NAME = "pyschunk_integrated"

## \brief Release name of the whole software project (a.k.a. as the \e "version" of the project).
#
#    \anchor project_release_pyschunk
#    The release name of the project.
#
#    A suffix of "-dev" indicates a work in progress, i.e. a not yet finished release.
#    A suffix of "-a", "-b", ... indicates a bugfix release.
#
#    From newest to oldest the releases have the following names and features:
#
#
#    - \b 5.3.0.3 2023-12-19
#      - copied to BKSTools/pyschunk as pyschunk_integrated
#
#    - \b 5.3.0.3 2023-12-06
#      - improved support for Linux

#
PROJECT_RELEASE = "5.3.0.3"

## \brief Date of the release of the software project.
#
#    \anchor project_date_pyschunk
#    The date of the release of the project.
#
PROJECT_DATE = "2023-12-19"
