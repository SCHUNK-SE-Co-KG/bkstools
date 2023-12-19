# -*- coding: UTF-8 -*-
'''
Created on 2019-06-04

@author: Dirk Osswald

@brief Provides the higher layer BKSModule class for access to SCHUNK BKS grippers via the HTTP/JSON webinterface.
'''

import time

from bkstools.bks_lib.bks_base import GetModbusSettings
from bkstools.bks_lib.bks_modbus import BKS_Modbus
from bkstools.bks_lib.debug import Print, ApplicationError, InsufficientReadRights
from bkstools.bks_lib.bks_http import BKS_HTTP
from pyschunk.generated.generated_enums import eCmdCode

class cDefault(object):
    def __init__(self):
        pass


    def __str__(self):
        '''return a string describing self
        '''
        return "Default"


    def __repr__(self):
        '''For more informative output in failed assertions: return a string describing self
        '''
        return "'Default'"

# A dummy object like None.
# To be used as parameter default value with the meaning "use the default stored in the class"
# Example usage:
# \code
#   class C(object):
#      def __init__( self ):
#         self.p = 42
#
#      def f( p=DEFAULT ):
#         if ( p is DEFAULT ):
#            p = self.p
#         ...
# \endcode
# c.f()    # will use p=c.p within c.f
# c.f( 1 ) # will use p=1   within c.f
DEFAULT = cDefault()


class GripperError( ApplicationError ):
    '''Class to represent errors signaled from the BKS gripper as exceptions.
    '''
    def __init__(self,args=None):
        ApplicationError.__init__(self,args)


class GripperWarning( ApplicationError ):
    '''Class to represent warnings signaled from the BKS gripper as exceptions.
    '''
    def __init__(self,args=None):
        ApplicationError.__init__(self,args)


class GripperTimeout( ApplicationError ):
    '''Class to represent timeout from the BKS gripper as exceptions.
    '''
    def __init__(self,args=None):
        ApplicationError.__init__(self,args)


def HandleWarningPrintOnly( gripper, msg="" ):
    """Print a verbose description of the warning but do not raise an Exception
    """
    ec = gripper.last_plc_sync_input[3] & 0x0000ffff
    wc = gripper.last_plc_sync_input[3]>>16
    try:
        wc_str = gripper.enums["wrn_code"].GetName(wc, "?" )
    except KeyError:
        wc_str = "?"
    try:
        ec_str = gripper.enums["err_code"].GetName(ec, "?" )
    except KeyError:
        ec_str = "?"

    print( f"""\n!Ignoring warning! {msg}
  plc_sync_input=[statusword={gripper.last_plc_sync_input[0]:08x}
                  actual_pos={gripper.last_plc_sync_input[1]}
                  reserved={gripper.last_plc_sync_input[2]:08x}
                  error_code={ec:04x} ({ec_str})
                  warning_code={wc:04x} ({wc_str}]""" )

    return False # do not raise an exception


class BKSModule( BKS_Modbus, BKS_HTTP ):
    """Convenience class to access SCHUNK BKS grippers via the Modbus or HTTP/JSON interface.
    BKSModule extends the interface provided by BKSBaseCommon, BKS_Modbus, and BKS_HTTP classes to simplify interaction with
    a gripper.

    The class provides some convenience functions to simplify writing of demos / tests
    """
    grip_from_outside = False
    grip_from_inside  = True

    def HandleTimeoutDefault( self, module, msg="" ):
        """Default handler for timeout. Raises GripperTimeout
        """
        raise GripperTimeout( msg )


    def HandleErrorDefault( self, module, msg="" ):
        """Default handler for error signaled from gripper. Raises GripperError
        """
        raise GripperError( msg )


    def HandleWarningDefault( self, module, msg="" ):
        """Default handler for warning signaled from gripper. Raises GripperWarning
        """
        raise GripperWarning( msg )


    def __init__( self, host,
                  max_age_in_s=5*60,
                  sleep_time=0.010,
                  handle_timeout=DEFAULT,
                  handle_warning=DEFAULT,
                  handle_error=DEFAULT,
                  debug=False,
                  repeater_timeout=3.0,
                  repeater_nb_tries=5 ):
        """CTor, see base class
        """
        modbus_settings = GetModbusSettings( host )

        # depending on the host parameter call the constructor of either BKS_Modbus or BKS_HTTP only:
        if ( modbus_settings ):
            BKS_Modbus.__init__( self, *modbus_settings, max_age_in_s, debug, repeater_timeout, repeater_nb_tries )
        else:
            # !!! Warning: somewhat dirty hack follows : !!!
            # In order to make method resolution work here we have to tweak the MRO (Method Resolution Order)
            # of our self. See https://stackoverflow.com/a/57820075/6098953
            # (Remark simply changing or replacing self.__class__.__mro__ does not work since it is a readonly tuple)

            # make shortcut to current MRO tuple:
            baseclasses_mro_tuple = self.__class__.__mro__

            # create a reordered MRO tuple:
            # - leaving out the not-need first element
            # - order of BKS_HTTP and BKS_Modbus exchanged

            # old style with fixed indices (cannot work when using further / future derived classes like demo_interrupt_movement.DemoMoveInterruptor)
            #new_mro   = (baseclasses_mro_tuple[2], baseclasses_mro_tuple[1], baseclasses_mro_tuple[3], baseclasses_mro_tuple[4] )

            # new, more flexible style with non fixed indices.
            # (FIXME: For further / future derived classes like demo_interrupt_movement.DemoMoveInterruptor
            #         this yields a
            #       > TypeError: Cannot create a consistent method resolution order (MRO) for bases BKS_Modbus, BKS_HTTP, BKSBaseCommon, object
            new_mro = ()
            for c in baseclasses_mro_tuple:
                if ( c is BKSModule ):
                    pass # reave out not-needed current class
                elif ( c is BKS_HTTP ):
                    new_mro += (BKS_Modbus,)
                elif ( c is BKS_Modbus ):
                    new_mro += (BKS_HTTP,)
                else:
                    new_mro += (c,)

            # Create a new class object with the new MRO:
            new_class = type( self.__class__.__name__, new_mro, dict( self.__class__.__dict__ ) )

            # Replace our class attribute with the created one:
            self.__class__ = new_class

            # Voila. self.SOME_METHOD will now search for SOME_METHOD in BKS_HTTP before BKS_Modbus as required.

            # Now we can call the base class constructor:
            BKS_HTTP.__init__( self, host, max_age_in_s, debug )

        self._cached_grp_vel = None
        self._cached_span = None
        self._cached_grp_prepos_delta = None

        self.wait_reference_timeout = 10.0       # todo: calculate from referencing velocity and maximum span
        #self.wait_command_received_timeout = 0.030
        self.wait_command_received_timeout = 0.300
        self.sleep_time           = sleep_time
        if ( handle_timeout is DEFAULT ):
            self.handle_timeout=self.HandleTimeoutDefault
        else:
            self.handle_timeout=handle_timeout

        if ( handle_error is DEFAULT ):
            self.handle_error=self.HandleErrorDefault
        else:
            self.handle_error=handle_error

        if ( handle_warning is DEFAULT ):
            self.handle_warning=self.HandleWarningDefault
        else:
            self.handle_warning=handle_warning

        self.StorePreCommandStatus()
        (self.controlword, self.pos, self.vel, self.force) = self.plc_sync_output  # cached values of last cyclic output data sent

    @property
    def last_statusword(self):
        return self.last_plc_sync_input[0]

    @property
    def last_actual_pos(self):
        return self.last_plc_sync_input[1]

    @property
    def last_warning_code(self):
        return self.last_plc_sync_input[3] >> 16

    @property
    def last_error_code(self):
        return self.last_plc_sync_input[3] & 0x0000ffff


    def Cached_span(self, force_reread=False ):
        """Return span of gripper in mm.
        Use a cached value if available and force_reread is False else read min_pos and max_pos from gripper
        """
        if ( self._cached_span is None ):
            self._cached_span = self.max_pos - self.min_pos
        return self._cached_span


    def Cached_grp_vel(self, force_reread=False ):
        """Return grp_vel of gripper in mm/s. Use a cached value if available and force_reread is False else read from gripper
        """
        if ( self._cached_grp_vel is None or self._cached_grp_vel == 0.0 ):
            try:
                self._cached_grp_vel = self.max_grp_vel
            except InsufficientReadRights:
                # grp_vel is readable by SERVICE only (doh?!)
                self._cached_grp_vel = self.min_vel #use minimum velocity to be on the save side
        return self._cached_grp_vel


    def Cached_grp_prepos_delta(self, force_reread=False ):
        """Return grp_prepos_delta of gripper. Use a cached value if available and force_reread is False else read from gripper
        """
        if ( self._cached_grp_prepos_delta is None ):
            self._cached_grp_prepos_delta = self.grp_prepos_delta
        return self._cached_grp_prepos_delta


    def StorePreCommandStatus(self):
        """read the plc_sync_input from the gripper and store in self.last_plc_sync_input
        self.pre_command_statusword will be set to the read statusword
        self.pre_command_received_toggle will be set to the command_received_toggle bit value of the statusword

        This must be called before any command is sent to the gripper in order to
        detect bit changes properly.
        """
        self.last_plc_sync_input = self.plc_sync_input
        self.pre_command_statusword = self.last_statusword
        self.pre_command_received_toggle = self.last_statusword & self.sw_command_received_toggle
        self.pre_command_t = time.time()


    def SendCyclic( self, controlword=DEFAULT, pos=DEFAULT, vel=DEFAULT, force=DEFAULT ):
        """Send cyclic data to the gripper
        If the controlword cw changes then StorePreCommandStatus() is called

        controlword - controlword to send or DEFAULT=use self.controlword
        pos  - position to send or DEFAULT=use self.pos
        vel  - velocity to snd or DEFAULT=use self.vel
        force  - force to send or DEFAULT=use self.force
        """
        if ( (not controlword is DEFAULT) and (controlword != self.controlword) ):
            self.StorePreCommandStatus()
            self.controlword = controlword

        if ( not pos is DEFAULT ):
            self.pos = pos

        if ( not vel is DEFAULT ):
            self.vel = vel

        if ( not force is DEFAULT ):
            self.force = force

        self.plc_sync_output = [ self.controlword, self.pos, self.vel, self.force ]


    def MakeReady( self ):
        """Make BKS gripper ready for operation, i.e. acknowledge any pending errors.

        self.wait_command_received_timeout will be used for the wait for command_received timeout
        0.300 s will be used for the wait for command_successfully_processed timeout

        Returns
        - True if the ready_for_operaiton bit is set within self.wait_timeout, else
          - If a new error was signaled by the gripper then the return value of self.handle_error() is returned.
          - If a new warning was signaled by the gripper then the return value of self.handle_warning() is returned.
          - on timeout, the return value of self.handle_timeout() is returned.
        """
        if ( self.last_statusword & self.sw_ready_for_operation
             and self.controlword == self.cw_fast_stop ):
            # Already ready_for_operation and controlword prepared => nothing to do
            return True

        if ( self.controlword & self.cw_acknowledge ):
            # The acknowledge bit is already set,
            # so just setting fast_stop and leaving acknowledge will not go to ready_for_operation
            # we have to set fast_stop alone first, wait and set acknowledge aditionally after that
            self.SendCyclic( controlword=self.cw_fast_stop )
            time.sleep( 0.1 )

        self.SendCyclic( controlword=self.cw_fast_stop | self.cw_acknowledge )

        t0 = time.time()
        ok = self.WaitFor_command_received_toggle()
        t1 = time.time()

        if ( ok ):
            # command_successfully_processed bit is unaffected by acknowledge now...
            ok = self.WaitForBits( self.sw_ready_for_operation | ((~self.pre_command_received_toggle) & self.sw_command_received_toggle),
                                   self.sw_ready_for_operation | self.sw_command_received_toggle,
                                   0.5, self.sleep_time )
            t2 = time.time()
            Print( f"Make ready command checked after {t0-self.pre_command_t:.3f}s, received after {t1-self.pre_command_t:.3f}s, read_for_operation after {t2-self.pre_command_t:.3f}s")

        return ok and bool(self.last_statusword & self.sw_ready_for_operation)


    def HandleWait( self, command_description, do_wait_for_command_successfully_processed, wait_command_successfully_processed_timeout ):
        """Helper to handle common wait for command_received_toggle and command_successfully_processed (if requested)
        """
        t0 = time.time()
        check_msg = f"command checked after {t0-self.pre_command_t:.3f}s"

        ok = self.WaitFor_command_received_toggle()
        t1 = time.time()
        if ( ok ):
            acknowledge_msg = f", command_received_toggle after {t1-self.pre_command_t:.3f}s"
        else:
            acknowledge_msg = f", failed to command_received_toggle after {t1-self.pre_command_t:.3f}s wait_command_received_timeout={self.wait_command_received_timeout:.3f}s"

        command_successfully_processed = False
        if ( ok and do_wait_for_command_successfully_processed ):
            command_successfully_processed = self.WaitFor_command_successfully_processed( wait_command_successfully_processed_timeout )
            t2 = time.time()

            if ( command_successfully_processed ):
                success_msg = f", command_successfully_processed after {t2-self.pre_command_t:.3f}s"
            else:
                success_msg = f", failed after {t2-self.pre_command_t:.3f}s command_successfully_processed_timeout={wait_command_successfully_processed_timeout}"
        else:
            success_msg = ""

        Print( f"{command_description} {check_msg}{acknowledge_msg}{success_msg}" )

        return ok and command_successfully_processed


    def reference( self, do_wait_for_command_successfully_processed=True ):
        """Send plc_sync_output to trigger a reference command

        REMARK: This command is no longer necessary and thus not available for user-level OPERATOR.

        The self.wait_command_received_timeout will be used for waiting for command_received_toggle to toggle
        If do_wait_for_command_successfully_processed is True then a timeout of self.wait_reference_timeout will be used for waiting for command_successfully_processed
        """

        self.command_code = eCmdCode.CMD_DETERMINE_BASE_ZERO_POS

        return self.HandleWait( "referene", do_wait_for_command_successfully_processed, self.wait_reference_timeout )


    def move_to_absolute_position( self, pos, vel, do_wait_for_command_successfully_processed=True, wait_command_successfully_processed_timeout=None ):
        """Send plc_sync_output to trigger a move_to_abs command
        \param pos - the absolute target position in µm
        \param vel - the target velocity in µm/s
        \param do_wait_for_command_successfully_processed - flag, if True then the call block until the command_successfully_processed bit is set or timeout or error or warning
                                           if False the call will return immediately after the command was received by the gripper

        The self.wait_command_received_timeout will be used for waiting for command_received_toggle to toggle
        If do_wait_for_command_successfully_processed is True then a timeout of wait_command_successfully_processed_timeout will be used for waiting for command_successfully_processed.
        If wait_command_successfully_processed_timeout is None then a timeout will be calculated from the distance and velocity times a safety factor of 1.2
        """
        if ( self.controlword & self.cw_move_to_absolute_position ):
            # a move_to_abs has been sent previously, so just toggle repeat_command_toggle:
            self.SendCyclic( controlword=self.controlword ^ self.cw_repeat_command_toggle,
                             pos=pos,
                             vel=vel )
        else:
            self.SendCyclic( controlword=self.cw_move_to_absolute_position | self.cw_fast_stop,
                             pos=pos,
                             vel=vel )

        if ( wait_command_successfully_processed_timeout is None ):
            wait_command_successfully_processed_timeout= 1.2 * abs( self.last_actual_pos - pos ) / vel + 0.3

        return self.HandleWait( "move_to_absolute_position", do_wait_for_command_successfully_processed, wait_command_successfully_processed_timeout )


    def move_to_relative_position( self, rpos, vel, do_wait_for_command_successfully_processed=True, wait_command_successfully_processed_timeout=None ):
        """Send plc_sync_output to trigger a move_relative command
        \param rpos - the relative target position in µm
        \param vel - the target velocity in µm/s

        The self.wait_command_received_timeout will be used for waiting for command_received_toggle to toggle
        If do_wait_for_command_successfully_processed is True then a timeout of wait_command_successfully_processed_timeout will be used for waiting for command_successfully_processed.
        If wait_command_successfully_processed_timeout is None then a timeout will be calculated from the distance and velocity times a safety factor of 1.2
        """
        if ( self.controlword & self.cw_move_to_relative_position ):
            # a move_to_rel has been sent previously, so just toggle repeat_command_toggle:
            self.SendCyclic( controlword=self.controlword ^ self.cw_repeat_command_toggle,
                             pos=rpos,
                             vel=vel )
        else:
            self.SendCyclic( controlword=self.cw_move_to_relative_position | self.cw_fast_stop,
                             pos=rpos,
                             vel=vel )

        if ( wait_command_successfully_processed_timeout is None ):
            wait_command_successfully_processed_timeout= 1.2 * abs( rpos ) / vel + 0.3

        return self.HandleWait( "move_to_relative_position", do_wait_for_command_successfully_processed, wait_command_successfully_processed_timeout )


    def grip_workpiece( self, direction, grip_velocity_ums, force_percent, do_wait_for_command_successfully_processed=True, wait_command_successfully_processed_timeout=None ):
        """Send plc_sync_output to trigger a grip_workpiece command
        \param direction - False = BKSModule.grip_from_outside means gripping from outside
               direction - True = BKSModule.grip_from_inside means gripping from inside
        \param grip_velocity_ums - the grip velocity in um/s
        \param force_percent- the force in percent
        """
        cmd = self.cw_grip_work_piece | self.cw_fast_stop
        if ( direction ):
            cmd |= self.cw_grip_direction
        self.SendCyclic( controlword=cmd, vel=grip_velocity_ums, force=force_percent )
        self._cached_grp_vel = grip_velocity_ums / 1000.0

        if ( wait_command_successfully_processed_timeout is None ):
            # simple approach assume we have to move the full span:
            #wait_command_successfully_processed_timeout= 1.2 * self.Cached_span() / self.Cached_grp_vel() + 0.3

            # optimization: consider actual position:
            if ( direction ):
                delta_pos_um = self.Cached_span()*1000.0 - self.last_actual_pos
            else:
                delta_pos_um = self.last_actual_pos
            vel_ums = self.Cached_grp_vel() * 1000.0
            wait_command_successfully_processed_timeout= 1.2 * delta_pos_um / vel_ums + 0.3

        self.HandleWait( "grip_workpiece", do_wait_for_command_successfully_processed, wait_command_successfully_processed_timeout )


    def grip_workpiece_with_expected_position( self, direction, position_um, velocity_ums, force_percent, do_wait_for_command_successfully_processed=True, wait_command_successfully_processed_timeout=None ):
        """Send plc_sync_output to trigger a grip_workpiece_with_expected_position command
        \param direction = False = BKSModule.grip_from_outside means gripping from outside
               direction = True = BKSModule.grip_from_inside means gripping from inside
        \param position_um - expected position in um
        \param velocity_ums - grip velocity in um/s
        \param force_percent - the force in %
        """
        cmd = self.cw_grip_workpiece_with_position | self.cw_fast_stop
        if ( direction ):
            cmd |= self.cw_grip_direction
        self.SendCyclic( controlword=cmd, pos=position_um, vel=velocity_ums, force=force_percent )
        self._cached_grp_vel = velocity_ums / 1000.0

        if ( wait_command_successfully_processed_timeout is None ):
            # if no timeout was given use actual_pos and expected pos
            #wait_command_successfully_processed_timeout= 1.2 * self.Cached_span() / min( velocity/1000.0, self.Cached_grp_vel() ) + 0.3

            delta_pos_um = abs( position_um - self.last_actual_pos )
            min_vel_ums =   min( velocity_ums, self.Cached_grp_vel()*1000.0 )
            wait_command_successfully_processed_timeout= 1.5 * (delta_pos_um / min_vel_ums) + 0.3

        self.HandleWait( "grip_workpiece_with_expected_position", do_wait_for_command_successfully_processed, wait_command_successfully_processed_timeout )


    def release_workpiece( self, do_wait_for_command_successfully_processed=True, wait_command_successfully_processed_timeout=None ):
        """Send plc_sync_output to trigger a release_workpiece command
        """
        cmd = self.cw_release_work_piece | self.cw_fast_stop
        self.SendCyclic( controlword=cmd )

        if ( wait_command_successfully_processed_timeout is None ):
            wait_command_successfully_processed_timeout= 1.2 * self.Cached_grp_prepos_delta() / self.Cached_grp_vel() + 0.3

        self.HandleWait( "release_workpiece", do_wait_for_command_successfully_processed, wait_command_successfully_processed_timeout )


    def WaitForBits( self,
                     expected,
                     mask,
                     wait_timeout, sleep_time ):
        """Wait until the masked bits change to the expected value in statusword

        wait_timeout is the time in seconds to wait for the bits to become expected, or:
        - If wait_timeout is None then use no timeout, i.e. wait forever
        - If wait_timeout is 0 then return after first try.

        sleep_time is the time in seconds to sleep before retrying, or:
        - if sleep_time is None or 0.0 then do not sleep before retrying

        Returns
        - True if the bits were equal to expected (not regarding error or warning bits), else
          - If a new error was signaled by the gripper then the return value of self.handle_error() is returned.
          - If a new warning was signaled by the gripper then the return value of self.handle_warning() is returned.
          - on timeout, the return value of self.handle_timeout() is returned.
        """
        #Print( f"mask={mask:08x} expected={expected:08x}" )

        #--- Check / initialize parameters:
        if ( wait_timeout is None ):
            wait_timeout = 99999.0  # use very long time (> 24h) for "forever"
        endtime = time.time() + wait_timeout

        if ( sleep_time is None ):
            sleep_time = 0.0


        #--- Wait for the bits to become expected:
        while True:
            self.last_plc_sync_input = self.plc_sync_input # update once per loop from gripper

            bits = self.last_statusword & mask
            #Print( f"bits={bits:08x}" )
            if ( bits == expected ):
                return True

            if (      (self.last_statusword & self.sw_error)
                 and ((self.pre_command_statusword & self.sw_error) == 0) ):
                # new error bit  detected:
                ec = self.last_plc_sync_input[3] & 0x0000ffff
                try:
                    ec_str = self.enums["err_code"].GetName(ec, "?" )
                except KeyError:
                    ec_str = "?"

                return self.handle_error( self, f"Error 0x{ec:02x} ({ec_str}) signaled while waiting for {expected:08x} with mask {mask:08x}" )

            if (      (self.last_statusword & self.sw_warning)
                 and ((self.pre_command_statusword & self.sw_warning) == 0) ):
                # new warning bit detected:
                wc = self.last_plc_sync_input[3]>>16
                try:
                    wc_str = self.enums["wrn_code"].GetName(wc, "?" )
                except KeyError:
                    wc_str = "?"

                self.handle_warning( self, f"Warning 0x{wc:02x} ({wc_str}) signaled while waiting for {expected:08x} with mask {mask:08x} " )
                # if handle_warning above did not raise an exception the ignore the warning and keep on waiting

            if ( endtime <= time.time() ):
                # timeout detected:
                return self.handle_timeout( self, f"Timeout signaled after {time.time()-(endtime-wait_timeout):.3}s while waiting for {expected:08x} with mask {mask:08x}" )

            if ( sleep_time > 0.0 ):
                time.sleep( sleep_time )


    def WaitFor_command_received_toggle( self ):
        """Wait until the gripper acknowledges that a new command was received,
        i.e. the command_received_toggle bit changes compared
        to self.pre_command_received_toggle

        This is a convenience function for WaitForBits(), see there for an explanation of the parameters

        The self.wait_command_received_timeout will be used as wait_timeout

        Returns True if the bit did toggle,
        else return value of one of the error/warning/timeout handler, see WaitForBits.
        """
        return self.WaitForBits( (~self.pre_command_received_toggle) & self.sw_command_received_toggle,
                                 self.sw_command_received_toggle,
                                 self.wait_command_received_timeout, self.sleep_time )


    def WaitFor_command_successfully_processed( self, wait_timeout ):
        """Wait until the gripper reports command_successfully_processed,
        i.e. ready_for_operaiton=1 and command_successfully_processed=1 and command_received_toggle changed compared to self.pre_command_received_toggle

        This is a convenience function for WaitForBits(), see there for an explanation of the parameters

        Returns True if the gripper signaled command_successfully_processed, else
        return value of one of the error/warning/timeout handler, see WaitForBits.
        """
        return self.WaitForBits( self.sw_ready_for_operation | self.sw_success | ((~self.pre_command_received_toggle) & self.sw_command_received_toggle),
                                 self.sw_ready_for_operation | self.sw_success | self.sw_command_received_toggle,
                                 wait_timeout, self.sleep_time )



    def WaitFor_position_reached( self, wait_timeout=None, sleep_time=None ):
        """Wait until the position reached bit gets set or wait_timeout.

        This is a convenience function for WaitForBits(), see there for an explanation of the parameters

        Returns True if the position_reached bit is set, else
        return value of one of the error/warning/timeout handler, see WaitForBits.
        """
        return self.WaitForBits( self.sw_position_reached,
                                 self.sw_position_reached,
                                 wait_timeout, sleep_time )
