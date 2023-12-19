# -*- coding: UTF-8 -*-
# @date: 2022-04-28 18:51
# @author: hsm2dot.exe 0.0.5.10 2022-04-27

import pyschunk.tools.util

# Enum for state id to state name mapping for SD_card
SD_card = pyschunk.tools.util.enum()
SD_card.Top_State    = 0
SD_card.Initializing = 1
SD_card.Running      = 2
SD_card.Idle         = 3
SD_card.Read         = 4
SD_card.Write        = 5
SD_card.Failure      = 6

# Enum for state id to state name mapping for application_state_machine
application_state_machine = pyschunk.tools.util.enum()
application_state_machine.Top_State                                 = 0
application_state_machine.Boot                                      = 1
application_state_machine.Error                                     = 2
application_state_machine.Operational                               = 4
application_state_machine.Prepare_for_Shutdown                      = 5
application_state_machine.Ready_for_Shutdown                        = 6
application_state_machine.Wait_Format                               = 7
application_state_machine.Boot_Start                                = 11
application_state_machine.Boot_Initialize_Parameters                = 12
application_state_machine.Factory_Reset                             = 29
application_state_machine.Wait_modules_shut_down_for_firmware_flash = 31
application_state_machine.Wait_Web_Content_Erased                   = 32

# Enum for state id to state name mapping for error_handler
error_handler = pyschunk.tools.util.enum()
error_handler.Top_State     = 0
error_handler.Wait_Setup    = 1
error_handler.Operate       = 2
error_handler.Stop          = 3
error_handler.Idle          = 20
error_handler.Wait_Read     = 21
error_handler.Wait_Written  = 22
error_handler.Factory_Reset = 23

# Enum for state id to state name mapping for HMS_Application_Statemachine
HMS_Application_Statemachine = pyschunk.tools.util.enum()
HMS_Application_Statemachine.Top_State                      = 0
HMS_Application_Statemachine.Appl_Init                      = 10
HMS_Application_Statemachine.Appl_Waitcom                   = 20
HMS_Application_Statemachine.Appl_Run                       = 30
HMS_Application_Statemachine.Appl_Run_Wait_for_Network_Type = 31
HMS_Application_Statemachine.Appl_Run_Normal_Mode           = 32
HMS_Application_Statemachine.Appl_Shutdown                  = 40
HMS_Application_Statemachine.Appl_ABCCReset                 = 50
HMS_Application_Statemachine.Appl_DevReset                  = 60
HMS_Application_Statemachine.Appl_Halt                      = 70

# Enum for state id to state name mapping for object_storage_block_device
object_storage_block_device = pyschunk.tools.util.enum()
object_storage_block_device.Top_State               = 0
object_storage_block_device.StartUp                 = 1
object_storage_block_device.Read_Object_Data        = 2
object_storage_block_device.Write_Object_Data       = 3
object_storage_block_device.Idle                    = 7
object_storage_block_device.Failure                 = 9
object_storage_block_device.StartUp_Read_Header     = 11
object_storage_block_device.StartUp_Read_Directory  = 12
object_storage_block_device.StartUp_Write_Header    = 13
object_storage_block_device.StartUp_Write_Directory = 14
object_storage_block_device.Migration_State         = 80
object_storage_block_device.Erase                   = 91

# Enum for state id to state name mapping for object_storage_flash_device
object_storage_flash_device = pyschunk.tools.util.enum()
object_storage_flash_device.Top_State                     = 0
object_storage_flash_device.Startup                       = 1
object_storage_flash_device.Read_Object_Data              = 2
object_storage_flash_device.Write_Object_Data             = 3
object_storage_flash_device.Idle                          = 4
object_storage_flash_device.Failure                       = 9
object_storage_flash_device.Startup_Read_Header           = 11
object_storage_flash_device.Startup_Read_Directory        = 12
object_storage_flash_device.Startup_Read_Object_Metadata  = 13
object_storage_flash_device.Startup_Write_Header          = 14
object_storage_flash_device.Startup_Write_Directory       = 15
object_storage_flash_device.Startup_Write_Object_Metadata = 16
object_storage_flash_device.Erase                         = 91

# Enum for state id to state name mapping for complex_brake_state_machine
complex_brake_state_machine = pyschunk.tools.util.enum()
complex_brake_state_machine.Top_State            = 0
complex_brake_state_machine.Brake_Init           = 1
complex_brake_state_machine.Brake_Deactive       = 2
complex_brake_state_machine.Hold_Workpiece_Motor = 3
complex_brake_state_machine.Hold_Workpiece_Brake = 4
complex_brake_state_machine.Hold_Position_Motor  = 5
complex_brake_state_machine.Hold_Position_Brake  = 6
