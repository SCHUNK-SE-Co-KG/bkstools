# -*- coding: UTF-8 -*-
#
# \brief Generated file with enum descriptions
# \author generate_hms_enum_description.exe 0.0.5.21 2022-10-24
# \date  2023-08-24 10:11
#
#  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#  ! DO NOT EDIT THIS FILE!                                      !
#  ! Anything changed here will be overwritten on the next build !
#  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from pyschunk.tools.util import enum

eMotorType = enum( MOTOR_DC=0,  # 0x00
        MOTOR_BLDC=1,  # 0x01
        MOTOR_PMSM=2,  # 0x02
        MOTOR_TORQUE=3,  # 0x03
        MOTOR_STEPPER=4,  # 0x04
        MAX_MOTORTYPE=5,  # 0x05
        )

eBksUserLevel = enum( OPERATOR=0,  # 0x00
        SERVICE=1,  # 0x01
        ROOT=2,  # 0x02
        NO_ACCESS=3,  # 0x03
        )

eFirmwareStorage = enum( FW_STORAGE_NONE=0,  # 0x00
        FW_STORAGE_CAN=1,  # 0x01
        FW_STORAGE_HMS=2,  # 0x02
        FW_STORAGE_SD=3,  # 0x03
        FW_STORAGE_IOL=4,  # 0x04
        FW_STORAGE_MB=5,  # 0x05
        )

eErrorCode = enum( ERR_NONE=0,  # 0x00
        ERR_NO_RIGHTS=3,  # 0x03
        INF_UNKNOWN_CMD=4,  # 0x04
        INF_FAILED=5,  # 0x05
        INF_WRONG_TYPE=18,  # 0x12
        INF_NO_AUTHORITY=20,  # 0x14
        INF_VAL_LIM_MAX=27,  # 0x1b
        INF_VAL_LIM_MIN=28,  # 0x1c
        ERR_BT_FAILED=40,  # 0x28
        ERR_MOT_TEMP_LO=108,  # 0x6c
        ERR_MOT_TEMP_HI=109,  # 0x6d
        ERR_LGC_TEMP_LO=112,  # 0x70
        ERR_LGC_TEMP_HI=113,  # 0x71
        ERR_LGC_VOLT_LO=114,  # 0x72
        ERR_LGC_VOLT_HI=115,  # 0x73
        ERR_MOT_VOLT_LO=116,  # 0x74
        ERR_MOT_VOLT_HI=117,  # 0x75
        ERR_REBOOT=124,  # 0x7c
        ERR_POWER_STAGE=126,  # 0x7e
        ERR_ZV_NOT_FOUND=137,  # 0x89
        ERR_ENC_PHASE=138,  # 0x8a
        ERR_ENC_SIN_LO=139,  # 0x8b
        ERR_ENC_SIN_HI=140,  # 0x8c
        ERR_ENC_COS_LO=141,  # 0x8d
        ERR_ENC_COS_HI=142,  # 0x8e
        ERR_ENC_SHORTCUT=143,  # 0x8f
        WRN_LGC_TEMP_LO=144,  # 0x90
        WRN_LGC_TEMP_HI=145,  # 0x91
        WRN_MOT_TEMP_LO=146,  # 0x92
        WRN_MOT_TEMP_HI=147,  # 0x93
        WRN_NOT_FEASIBLE=148,  # 0x94
        WRN_LGC_VOLT_LO=150,  # 0x96
        WRN_LGC_VOLT_HI=151,  # 0x97
        WRN_MOT_VOLT_LO=152,  # 0x98
        WRN_MOT_VOLT_HI=153,  # 0x99
        WRN_FLASH_FAILED=155,  # 0x9b
        WRN_ERASE_FAILED=156,  # 0x9c
        WRN_FACT_FAILED=157,  # 0x9d
        WRN_AUTH_FAILED=158,  # 0x9e
        WRN_SD_NOT_PREP=159,  # 0x9f
        WRN_NO_PART=161,  # 0xa1
        ERR_ENC_PULSES=180,  # 0xb4
        ERR_ENC_NO_INDEX=181,  # 0xb5
        ERR_ENC_MN_INDEX=182,  # 0xb6
        ERR_ENC_HALL_ILL=183,  # 0xb7
        ERR_ENC_NO_HALL=184,  # 0xb8
        ERR_CHP_TIMEOUT=186,  # 0xba
        ERR_CHP_FAILED=187,  # 0xbb
        ERR_INVAL_PHRASE=212,  # 0xd4
        ERR_SOFT_LOW=213,  # 0xd5
        ERR_SOFT_HIGH=214,  # 0xd6
        ERR_FAST_STOP=217,  # 0xd9
        ERR_CURRENT=222,  # 0xde
        ERR_I2T=223,  # 0xdf
        ERR_INTERNAL=225,  # 0xe1
        ERR_TOO_FAST=228,  # 0xe4
        ERR_FLASH_FAILED=231,  # 0xe7
        ERR_COMM_LOST=239,  # 0xef
        ERR_REF_ABORT_TO=240,  # 0xf0
        ERR_MOV_ABORT_TO=241,  # 0xf1
        ERR_NO_REF=242,  # 0xf2
        ERR_MOVE_BLOCKED=244,  # 0xf4
        ERR_UNKNOWN_HW=245,  # 0xf5
        ERR_BLOCK_FAILED=246,  # 0xf6
        ERR_NO_COMM=247,  # 0xf7
        ERR_WRONG_HW=248,  # 0xf8
        ERR_WRONG_MODULE=249,  # 0xf9
        ERR_SD_FAILED=250,  # 0xfa
        ERR_FLASH_LOST=251,  # 0xfb
        ERR_SW_COMM=252,  # 0xfc
        )

eGripperType = enum( EGI_40=0,  # 0x00
        EGI_80=1,  # 0x01
        EGL2_90=2,  # 0x02
        UG4_DIO_80=3,  # 0x03
        EGL_C=4,  # 0x04
        EGH=5,  # 0x05
        EGU_50_N_B=6,  # 0x06
        EGU_60_N_B=7,  # 0x07
        EGU_70_N_B=8,  # 0x08
        EGU_80_N_B=9,  # 0x09
        EGU_50_M_B=10,  # 0x0a
        EGU_60_M_B=11,  # 0x0b
        EGU_70_M_B=12,  # 0x0c
        EGU_80_M_B=13,  # 0x0d
        EGK_25_N_B=14,  # 0x0e
        EGK_40_N_B=15,  # 0x0f
        EGK_50_N_B=16,  # 0x10
        EGK_25_M_B=17,  # 0x11
        EGK_40_M_B=18,  # 0x12
        EGK_50_M_B=19,  # 0x13
        EGU_50_N_SD=20,  # 0x14
        EGU_60_N_SD=21,  # 0x15
        EGU_70_N_SD=22,  # 0x16
        EGU_80_N_SD=23,  # 0x17
        EGU_50_M_SD=24,  # 0x18
        EGU_60_M_SD=25,  # 0x19
        EGU_70_M_SD=26,  # 0x1a
        EGU_80_M_SD=27,  # 0x1b
        )

eBksReferencingType = enum( MOVE_INSIDE=0,  # 0x00
        MOVE_OUTSIDE=1,  # 0x01
        MOVE_OUT_MEAS_IN=2,  # 0x02
        MOVE_IN_MEAS_OUT=3,  # 0x03
        )

eFieldbusType = enum( UNKNOWN=0,  # 0x00
        PROFINET=1,  # 0x01
        EtherNet_IP__TM_=2,  # 0x02
        EtherCAT=3,  # 0x03
        Modbus_TCP=4,  # 0x04
        Common_Ethernet=5,  # 0x05
        IOLink=6,  # 0x06
        Modbus_RTU=7,  # 0x07
        )

eBrakeChopperMode = enum( DISABLED=0,  # 0x00
        ENABLED=1,  # 0x01
        )

schunk_ds_state_properties_t = enum( eDS_INITIAL=0,  # 0x00
        eDS_RESERVED_1=1,  # 0x01
        eDS_UPLOAD=2,  # 0x02
        eDS_DOWNLOAD=4,  # 0x04
        eDS_LOCKED=6,  # 0x06
        eDS_RESERVED_2=120,  # 0x78
        eDS_UPLOAD_FLAG=128,  # 0x80
        )

