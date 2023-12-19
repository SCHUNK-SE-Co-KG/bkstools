# -*- coding: UTF-8 -*-
"""
\file
\section pyschunk_tools_pytime_general General file information

  \author   Dirk Osswald
  \date     2015-04-30

\brief
  Slightly enhanced standard time module which tries to use the correct timezone.

  \attention
    To make this work this module must be included previous to any
    import of the standard time module!

   Typical usage:
   \code
     import pyschunk.tools.pytime  # @UnusedImport  must be done first
     import time

     #access time.X as always
   \endcode
\section pyschunk_tools_pytime_copyright Copyright

- Copyright (c) 2015 SCHUNK GmbH & Co. KG

<HR>
\internal

  \subsection pyschunk_tools_pytime_details SVN related, detailed file specific information:
    $LastChangedBy: Osswald2 $
    $LastChangedDate: 2015-02-02 17:00:53 +0100 (Mon, 02 Feb 2015) $
    \par SVN file revision:
      $Id$

\subsection pyschunk_tools_pytime_changelog Changelog of this file:
    \include pytime.py.log
"""
####################################################################

import os
#print( 'pyschunk.tools.pytime: os.environ["TZ"]=%r' % (os.environ["TZ"],) )
try:
    # Delete the TZ timezone environment variable as windows' native python does not seem to handle it correctly:
    del os.environ["TZ"]
except KeyError:
    pass
