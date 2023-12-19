'''
Created on 06.09.2018

@author: Dirk Osswald

Generic logging using the standard python logging module.

By default logging messages are silenced and do not appear anywhere.
This is mainly for backwards compatibility.
But this can be changed in multiple ways:
- For all scripts using this mylogger by providing a YAML config file.
  The YAML config file is searched either in the standard location or
  in a location indicated by an environment variable, by default
  named 'LOG_CFG'.
  The standard location on Windows is "c:\pyschunk_logging\config.yaml"
  and "~/pyschunk_loggin/config.yaml" on Linux
- For a specific script by modifiying pyschunk.tools.mylogger.g_default_config_settings
  after the import and before the pyschunk.tools.mylogger.setupLogging() is called.

The configuration there can be widely adjusted. E.g. the logging can
be set to the console, or to files or files with limited size and file rotation
or even to log via network...
'''

#sources: https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/

# remarks:
# - logging.config.fileConfig is outdated and deprecated according to
#   https://docs.python.org/2/library/logging.config.html#object-connections
#   so use newer dictConfig and read settings from a file.
# - since json files do not understand comments let's use yaml

import os
import logging               # @UnusedImport
import logging.config
import yaml
import platform

# Default configuration settings:
#  For now: nothing is logged to console or file or whatever. For backwards compatibility
g_default_config_settings = {
        'version': 1,
        'disable_existing_loggers': False,  # invalidates previous logger config settings
        'formatters': {
            'standard': {
                'format': '%(process)d %(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'short': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'very_short': {
                'format': '[%(levelname)s] %(message)s'
            },
        },
        'handlers': {
            'silent' : {                             # the do-nothing handler
                'class'     : 'logging.NullHandler',
            },
            'console': {                             # the print-to-console handler
                #'level'     :'INFO',
                'class'     :'logging.StreamHandler',
                'formatter' :'standard',
            },
            'console_very_short': {                  # the print-to-console handler in very short format
                'level'     :'DEBUG',
                'class'     :'logging.StreamHandler',
                'formatter' :'very_short',
            },
        },
        'loggers': {
            '': {
                'handlers' : ['silent'],
                #'handlers' : ['console'],
                #'level'    : 'INFO',
                'level'    : 'DEBUG',
                #'level'    : 'ERROR',
                'propagate': True
            }
        }
    }


def getLogger( name ):
    '''Just return the standard logging.getLogger() for now.
    Maybe we'll do more in the future
    '''
    return logging.getLogger( name )


if ( platform.system() == "Linux" ):
    c_default_config_file_path = os.path.expanduser( '~/pyschunk_logging/config.yaml' )
else:
    c_default_config_file_path = 'c:/pyschunk_logging/config.yaml'


def setupLogging( config_file_path=c_default_config_file_path,
                  env_key='LOG_CFG' ):
    """Setup logging configuration.
    If the environment defines a variable with name given in env_key (which
    defaults to "LOG_CFG") then the value of that environment variable is
    used as the file name for the config file and overwrites the config_file_path.
    Configuration is read from a yaml file config_file_path. If the
    file is not available then the g_default_config_settings are used instead
    """
    path = config_file_path
    value = os.getenv(env_key, None)
    #print( f"trying logging config file {path}")
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
        #print( f"used logging config file {config_file_path}")
    else:
        global g_default_config_settings
        logging.config.dictConfig(g_default_config_settings)
        #print( f"used default logging config")


class cLoggerFileLikeObject( object ):
    """Class that wraps a logger method like logger.info into a file like object.
    This allows to call write() and flush() on cLoggerFileLikeObject objects
    """
    def __init__(self, logger_method):
        self.logger_method = logger_method

    def write(self, msg ):
        if (msg.endswith( '\r\n' ) ):
            msg = msg[:-2]
        elif (msg.endswith( '\n' ) ):
            msg = msg[:-1]
        self.logger_method( msg )

    def flush(self):
        pass


def runMain( the_name, the_main, the_logger ):
    '''Convenience function to run the_main function and log exceptions / normal termination with the_logger.

    This is a replacement for:
    \code
      if __name__ == '__main__':
        main()
    \endcode

    Usage:
    \code
      import pyschunk.tools.mylogger
      logger = pyschunk.tools.mylogger.getLogger( "YOUR-SCRIPT-NAME" )
      pyschunk.tools.mylogger.setupLogging()
      ...
      def main():
        ...

      pyschunk.tools.mylogger.runMain( __name__, main, logger )
    \endcode
    '''
    if ( the_name == '__main__' ):
        try:
            the_main()
        except (SystemExit, KeyboardInterrupt) as e:
            the_logger.debug('Terminated normally with %r' % e)
            raise
        except Exception as e:
            the_logger.error('Terminated with exception:', exc_info=True)
            raise
        else:
            the_logger.debug('Terminated normally')
