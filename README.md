# BKSTools

[![Build Python Wheel](https://github.com/kcinnaySte/bkstools/actions/workflows/build_wheel.yml/badge.svg)](https://github.com/kcinnaySte/bkstools/actions/workflows/build_wheel.yml)

BKSTools is a Python package for communicating with newer SCHUNK grippers like EGU and EGK. These grippers are called BKS grippers
since they use the SCHUNK **B**au**K**asten**S**oftware.
The BKSTools provide ready-to-use command line scripts and an API to interact with the BKS grippers from your own Python code.

## Installation

A Python installation of version 3.7 or above is required. The installation of Python itself is not described here, see e.g. https://www.python.org/ for details.

The installation of the bkstools package using pip, the python package manager, is described below.

### Packages
For now SCHUNK provides prebuilt packages for the [pip](https://pypi.org/project/pip/) python package manager on request only. These packages are called "wheels" and have a *.whl file extension.

#### Package generation
For generating the *.whl package file on your own you can download the whole project from https://github.com/SCHUNK-SE-Co-KG/bkstools.git or simply clone it from there.
To clone it use:
```bash
git clone https://github.com/SCHUNK-SE-Co-KG/bkstools.git
```

To generate the package using a python virtual environment you can use:
```bash
cd bkstools
make venv
make bdist_wheel
```
This will generate e.g. `dist/bkstools-0.0.2.25-py3-none-any.whl`.

#### Package installation using pip

For the following description lets assume that you have something like the following file:
- `PATH_TO/bkstools-0.0.2.25-py3-none-any.whl`

The PATH_TO and the version numbers may of course vary.

### Virtual environment
It is not strictly necessary but still recommended to install the provided packages in a so called "virtual python environment", see e.g. https://docs.python.org/3/library/venv.html
This separates the dependencies of the BKSTools from other python programs on your computer.

To set up the virtual environment in *Linux* use something like the following in a shell:
```bash
mkdir bkstools             # create a directory
cd bkstools                # enter that directory
python3 -m venv venv       # create the virtual environment (mostly empty for now)
source venv/bin/activate   # activate the new virtual environment
```

On *Windows* use something like the following in a "cmd" console window:
```bash
md bkstools                # create a directory
cd bkstools                # enter that directory
python -m venv venv        # create the virtual environment (mostly empty for now)
venv\Scripts\activate.bat  # activate the new virtual environment
```

### Package installation
To install the actual BKSTools package use:

On Linux:
```pip install PATH_TO/pyschunk-5.3.0.3-py3-none-any.whl PATH_TO/bkstools-0.0.2.24-py3-none-any.whl```

On Windows:
```pip install PATH_TO\pyschunk-5.3.0.3-py3-none-any.whl PATH_TO\bkstools-0.0.2.24-py3-none-any.whl```

Of course you have to adjust the `PATH_TO` parts to point to your downloaded *.whl files.

## Usage
The installation above makes some ready-to-use command line (and GUI) tools available (in the activated virtual environment).
Additionally the bkstools is available as a python import module ready to be used by your own python scripts.

### Background and prerequisites
For communicating with a gripper the BKSTools use one of the following channels:
- Ethernet using the TCP/HTTP/JSON web-interface for grippers with EtherNet/IP, ProfiNet or EtherCAT interface. (For EtherCAT see restrictions below).
- Modbus-RTU for grippers with RS485 / Modbus-RTU interface

The former simply requires a standard ethernet interface on your computer running the BKSTools.
The latter usually requires additional hardware to interface to the physical RS485 interface that is used by the Modbus-RTU gripper. Such hardware can be e.g. a USB to RS485 interface board.
These typically show up as "serial devices", i.e. a "COM" port like "COM1, COM2, ..." on Windows or a "tty" device like "/dev/ttyS0, /dev/ttyUSB0, ..." on Linux.

#### Ethernet based communication
The BKSTools do *not* use the industrial ethernet protocols like Profinet, EtherNet/IP or EtherCAT of a BKS gripper. Instead the BKSTools can use
the additional "Service-Ethernet" communication channel of ethernet based BKS grippers. That means it uses HTTP GET and POST requests
to exchange JSON data with the gripper. This works for SCHUNK BKS grippers with a TCP/IP based Ethernet communication like Profinet and EtherNet/IP.
While EtherCAT still uses Ethernet it does not provide TCP/IP services per se, so the BKSTools can communicate with an EtherCAT SCHUNK gripper only
if it can use Ethernet over EtherCAT (EoE), which must be provided by an additional EtherCAT master (not provided by SCHUNK), usually a PLC.

The HTTP protocol relies on TCP/IP and thus the BKS gripper must already have a valid IP-address in order to be accessed by the BKSTools.
The gripper can be configured to have a fixed IP or it can be configured to use DHCP to get a valid IP-address. See the gripper documentation
on how to configure that.

#### Modbus-RTU communication
For grippers with RS485 / Modbus-RTU interface the BKSTools can use the Modbus-RTU protocol via a "serial port". Here the BKSTools use the "Fieldbus" interface of the gripper.

### Calling convention

If you "installed" the BKSTools package with ```pip``` as described above then wrappers for the original ```*.py``` scripts from the BKSTools package were installed
to the ```PATH``` (in the virtual python environment). The BKSTools scripts are then available without a ```.py``` suffix.
The examples shown below assume that you have installed the packages.

### Getting help
The scripts are directly callable from the command line. All scripts provide an integrated help message which biefly describes their purpose and usage.
That help message can be shown by calling ```SCRIPT_NAME -h```. Example:
```bash
> bks -h
usage: bks.py [-h] [-v] [-H HOST] [--force_reread] [--debug] [--debug_sleep] [--repeat_timeout REPEAT_TIMEOUT]
              [--repeat_nb_tries REPEAT_NB_TRIES] [-l] [-p PERIOD] [-D DURATION] [--gpd] [--absolute_time]
              [--gpdtitle GPD_TITLE] [-o OUTPUT_FILE_NAME_WITHOUT_SUFFIX] [--separator SEPARATOR] [--use_comma]
              [other ...]

Read and/or write parameters of a SCHUNK BKS gripper (like EGI/EGU/EGK) according to the parameters given.

Example usage:
- bks.py -H 10.49.57.13 --list
- bks.py -H 10.49.57.13 actual_pos
- bks.py -H 10.49.57.13 actual_pos set_pos=25.4
- bks.py -H 10.49.57.13 actual_pos plc_sync_output plc_sync_input system_state internal_params.comm_state -D -10.0 --gpd
- bks.py -H COM2 serial_no_num serial_no_num:08x
- bks.py -H COM3,12,19200 set_pos=12.34
- bks.py -H /dev/ttyUSB0 sw_build_date

positional arguments:
  other                 list of space separated firmware parameter names to read and/or write, e.g. 'actual_pos set_pos=4.5'.
                        For structured parameters you can access a single element for reading or writing by giving the name as
                        PARAMETERNAME.ELEMENTNAME like in 'plc_sync_input.actual_velocity' or
                        'plc_sync_output.control_dword=0x1245678'. For structured parameters you can access the whole
                        parameter for writing by giving the value as a tuple like in 'plc_sync_output="(11,22,33,44)"'. The
                        number of values in the tuple must match the number of elements in the structured parameter.
                        By adding ":FORMAT" the output format of a parameter can changed. For example to output a value as hex
                        with leading zeros add ":04x" to the parametername. The syntax for the FORMAT is the one used for
                        python f-strings or string.format().
                        Try option --list to get a list of all parameter names.

options:
  -h, --help            show this help message and exit
  -v, --version         Print the version and exit.
  -H HOST, --host HOST  "The BKS module to connect to.
                        For modules connected via ethernet this is the name or IP of the host to connect to.
                        For modules connected via Modbus/RS485 this is a string of the form
                        "SERIAL_INTERFACE,SLAVE_ID,BAUDRATE,COM_SETTINGS".
                        SERIAL_INTERFACE is the serial interface to use like "COM1" on Windows or "/dev/ttyUSB0" on Linux
                        SLAVE_ID is the Modbus slave ID of the module (optional, default used by our modules is 12)
                        BAUDRATE is the RS485 baudrate in bit/s (optional, default used by our modules is 115200)
                        COM_SETTINGS must be 8E1 for now (8 data bits, Even parity, 1 stop-bit)
                        SLAVE_ID, BAUDRATE and COM_SETTINGS may be left out and default to 12, 115200 and 8E1 respectively
                        then. A SLAVE_ID of 0 means "broadcast" and addresses all slaves. Only valid when writing values.
                        Example: --host COM6,15,9600
                        If not given then the value of the BKS_HOST environment variable is considered instead.
...
 ```

### Specifying communication parameters

All scripts need to know the "host", i.e. the address of the BKS gripper to access. You can provide this via the ```-H``` (capital "H") command line argument.
Pro-Tip: To save you typing this over and over again you can set the `BKS_HOST` environment variable. If no `-H` is given then the value of the `BKS_HOST` environment variable is used.
For Ethernet based grippers the host is an alphanumeric DNS-hostname or an IPv4-address.
For Modbus-RTU based grippers the host is a description of how to access the gripper via a serial interface


#### Ethernet based communication

Assuming that your BKS gripper is available at IP 10.49.57.13:
- On Linux:
  ```bash
  export BKS_HOST=10.49.57.13
  ```
- On Windows:
  ```bash
  set BKS_HOST=10.49.57.13
  ```


#### Serial / RS485 / Modbus-RTU based communication

Assuming that your BKS gripper is available via Modbus-RTU/RS485 on /dev/ttyUSB0 (Linux) or COM1 (Windows) as Slave-ID 12 with baudrate 115200 and communication parameters 8E1 (8 data bits, Even parity, 1 stop bit):
- On Linux:
  ```bash
  export BKS_HOST=/dev/ttyUSB0,12,115200,8E1
  ```
- On Windows:
  ```bash
  set BKS_HOST=COM1,12,115200,8E1
  ```

If using the default values for slave-ID (12), baudrate (115200) and communication parameters (8E1) then these need not be provided. So the above setting can be shortened to:

- On Linux:
  ```bash
  export BKS_HOST=/dev/ttyUSB0
  ```
- On Windows:
  ```bash
  set BKS_HOST=COM1
  ```


### Command line tools
The following scripts do not have a grahpical user interface (GUI).
They just write output to the console on stdout (and sometimes read input from keyboard via stdin).

- General purpose scripts (for interactive use or to be called from other scripts):
  - ```bks```      Read and/or write parameters of a BKS gripper. The script can do cyclic reading.
  - ```bks_move``` Move a BKS gripper to an absolute or relative position
  - ```bks_grip``` Grip (or release) a workpiece with a BKS gripper
  - ```bks_get_system_messages``` Get all or selected system messages of a BKS gripper


- Demonstration scripts (for demonstration to show the use of the API mainly):
  - ```demo_simple``` Simple basic control (move, grip, release) of a SCHUNK BKS gripper using the basic ```BKSBase``` interface class.
  - ```demo_bks_grip_outside_inside``` Perform a cycle of outside-gripping, releasing, inside-gripping, releasing with BKS gripper using the
    more advanced ```BKSModule``` interface class
  - ```demo_grip_workpiece_with_expected_position``` Perform a cycle of grip and release movements with a BKS gripper using the
    more advanced ```BKSModule``` interface class and the additional grip-with-expected-workpiece-positon gripping command.


**WARNING The scripts provided are for demonstration purposes only. The do not include extensive error handling or proper saftey considerations!**


### GUI tools
The following commands do have a GUI. Nonetheless the initial parameters must be provided via command line options.

- ```bks_jog```     Simple interactive moving of a BKS gripper in absolute position, relative position or jog mode.
- ```bks_status```  Simple interactive display of cyclic data of a BKS gripper, including control- and statusword.

### API

There are two interface classes to interact with a BKS gripper:
- ```BKSBase```   Basic interaction, provides all parameters of a BKS gripper as properties of a Python object.
- ```BKSModule``` Advanced interaction which (partly) implements the bit-based protocol for exchanging cyclic data with the BKS gripper like a "regular PLC" would do.

No further examples and descriptions are given here. For more details see the demonstration programs and of course the
doc-strings of the API methods. Use the well commented ```bkstools\demo\demo_simple.py``` as starting point and then the slightly more advanced
```bkstools\demo\demo_grip_workpiece_with_expected_position.py``` for a more realistic example.


## Contributing
Feedback is welcome (on the code as well as on the documentation).
