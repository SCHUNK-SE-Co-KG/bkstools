# -*- coding: UTF-8 -*-
'''
The HMS datatypes from abp.h
Created on 18.10.2018

@author: Dirk Osswald
'''
from pyschunk.tools.util import enum

HMS_Datatypes = enum( ABP_BOOL                    =0, # Boolean
                      ABP_SINT8                   =1, #/* Signed 8 bit integer          */
                      ABP_SINT16                  =2, #/* Signed 16 bit integer         */
                      ABP_SINT32                  =3, #/* Signed 32 bit integer         */
                      ABP_UINT8                   =4, #/* Unsigned 8 bit integer        */
                      ABP_UINT16                  =5, #/* Unsigned 16 bit integer       */
                      ABP_UINT32                  =6, #/* Unsigned 32 bit integer       */
                      ABP_CHAR                    =7, #/* Character                     */
                      ABP_ENUM                    =8, #/* Enumeration                   */
                      ABP_BITS8                   =9, #/* 8 bit bitfield (ABCC40)       */
                      ABP_BITS16                  =10, #/* 16 bit bitfield (ABCC40)      */
                      ABP_BITS32                  =11, #/* 32 bit bitfield (ABCC40)      */
                      ABP_OCTET                   =12, #/* 8 bit data (ABCC40)           */

                      ABP_SINT64                  =16, #/* Signed 64 bit integer         */
                      ABP_UINT64                  =17, #/* Unsigned 64 bit integer       */
                      ABP_FLOAT                   =18, #/* Floating point/real number    */

                      ABP_PAD0                    =32, #/* Padding bitfield (ABCC40)     */
                      ABP_PAD1                    =33, #/* Padding bitfield (ABCC40)     */
                      ABP_PAD2                    =34, #/* Padding bitfield (ABCC40)     */
                      ABP_PAD3                    =35, #/* Padding bitfield (ABCC40)     */
                      ABP_PAD4                    =36, #/* Padding bitfield (ABCC40)     */
                      ABP_PAD5                    =37, #/* Padding bitfield (ABCC40)     */
                      ABP_PAD6                    =38, #/* Padding bitfield (ABCC40)     */
                      ABP_PAD7                    =39, #/* Padding bitfield (ABCC40)     */
                      ABP_PAD8                    =40, #/* Padding bitfield (ABCC40)     */
                      ABP_PAD9                    =41, #/* Padding bitfield (ABCC40)     */
                      ABP_PAD10                   =42, #/* Padding bitfield (ABCC40)     */
                      ABP_PAD11                   =43, #/* Padding bitfield (ABCC40)     */
                      ABP_PAD12                   =44, #/* Padding bitfield (ABCC40)     */
                      ABP_PAD13                   =45, #/* Padding bitfield (ABCC40)     */
                      ABP_PAD14                   =46, #/* Padding bitfield (ABCC40)     */
                      ABP_PAD15                   =47, #/* Padding bitfield (ABCC40)     */
                      ABP_PAD16                   =48, #/* Padding bitfield (ABCC40)     */

                      ABP_BOOL1                   =64, #/* 1 bit boolean (ABCC40)        */
                      ABP_BIT1                    =65, #/* 1 bit bitfield (ABCC40)       */
                      ABP_BIT2                    =66, #/* 2 bit bitfield (ABCC40)       */
                      ABP_BIT3                    =67, #/* 3 bit bitfield (ABCC40)       */
                      ABP_BIT4                    =68, #/* 4 bit bitfield (ABCC40)       */
                      ABP_BIT5                    =69, #/* 5 bit bitfield (ABCC40)       */
                      ABP_BIT6                    =70, #/* 6 bit bitfield (ABCC40)       */
                      ABP_BIT7                    =71, #/* 7 bit bitfield (ABCC40)       */
                      )

HMS_Datatypes_size_in_bytes = {     HMS_Datatypes.ABP_BOOL:1,
                                    HMS_Datatypes.ABP_SINT8:1,
                                    HMS_Datatypes.ABP_SINT16:2,
                                    HMS_Datatypes.ABP_SINT32:4,
                                    HMS_Datatypes.ABP_UINT8:1,
                                    HMS_Datatypes.ABP_UINT16:2,
                                    HMS_Datatypes.ABP_UINT32:4,
                                    HMS_Datatypes.ABP_CHAR:1,
                                    HMS_Datatypes.ABP_ENUM:1,
                                    HMS_Datatypes.ABP_BITS8:1,
                                    HMS_Datatypes.ABP_BITS16:2,
                                    HMS_Datatypes.ABP_BITS32:4,
                                    HMS_Datatypes.ABP_OCTET:1,
                                    HMS_Datatypes.ABP_SINT64:8,
                                    HMS_Datatypes.ABP_UINT64:8,
                                    HMS_Datatypes.ABP_FLOAT:4,
#                                     HMS_Datatypes.ABP_PAD0:1,
#                                     HMS_Datatypes.ABP_PAD1:1,
#                                     HMS_Datatypes.ABP_PAD2:1,
#                                     HMS_Datatypes.ABP_PAD3:1,
#                                     HMS_Datatypes.ABP_PAD4:1,
#                                     HMS_Datatypes.ABP_PAD5:1,
#                                     HMS_Datatypes.ABP_PAD6:1,
#                                     HMS_Datatypes.ABP_PAD7:1,
#                                     HMS_Datatypes.ABP_PAD8:1,
#                                     HMS_Datatypes.ABP_PAD9:1,
#                                     HMS_Datatypes.ABP_PAD10:1,
#                                     HMS_Datatypes.ABP_PAD11:1,
#                                     HMS_Datatypes.ABP_PAD12:1,
#                                     HMS_Datatypes.ABP_PAD13:1,
#                                     HMS_Datatypes.ABP_PAD14:1,
#                                     HMS_Datatypes.ABP_PAD15:1,
#                                     HMS_Datatypes.ABP_PAD16:1,
#                                     HMS_Datatypes.ABP_BOOL1:1,
#                                     HMS_Datatypes.ABP_BIT1:1,
#                                     HMS_Datatypes.ABP_BIT2:1,
#                                     HMS_Datatypes.ABP_BIT3:1,
#                                     HMS_Datatypes.ABP_BIT4:1,
#                                     HMS_Datatypes.ABP_BIT5:1,
#                                     HMS_Datatypes.ABP_BIT6:1,
#                                     HMS_Datatypes.ABP_BIT7:1 )
                                }
HMS_ErrorCodes = enum( ABP_ERR_NO_ERROR            = 0x00,    # /* No error                         */
                       ABP_ERR_INV_MSG_FORMAT      = 0x02,    # /* Invalid message format           */
                       ABP_ERR_UNSUP_OBJ           = 0x03,    # /* Unsupported object               */
                       ABP_ERR_UNSUP_INST          = 0x04,    # /* Unsupported instance             */
                       ABP_ERR_UNSUP_CMD           = 0x05,    # /* Unsupported command              */
                       ABP_ERR_INV_CMD_EXT_0       = 0x06,    # /* Invalid CmdExt[ 0 ]              */
                       ABP_ERR_INV_CMD_EXT_1       = 0x07,    # /* Invalid CmdExt[ 1 ]              */
                       ABP_ERR_ATTR_NOT_SETABLE    = 0x08,    # /* Attribute access is not set-able */
                       ABP_ERR_ATTR_NOT_GETABLE    = 0x09,    # /* Attribute access is not get-able */
                       ABP_ERR_TOO_MUCH_DATA       = 0x0A,    # /* Too much data in msg data field  */
                       ABP_ERR_NOT_ENOUGH_DATA     = 0x0B,    # /* Not enough data in msg data field*/
                       ABP_ERR_OUT_OF_RANGE        = 0x0C,    # /* Out of range                     */
                       ABP_ERR_INV_STATE           = 0x0D,    # /* Invalid state                    */
                       ABP_ERR_NO_RESOURCES        = 0x0E,    # /* Out of resources                 */
                       ABP_ERR_SEG_FAILURE         = 0x0F,    # /* Segmentation failure             */
                       ABP_ERR_SEG_BUF_OVERFLOW    = 0x10,    # /* Segmentation buffer overflow     */
                       ABP_ERR_VAL_TOO_HIGH        = 0x11,    # /* Written data value is too high (ABCC40) */
                       ABP_ERR_VAL_TOO_LOW         = 0x12,    # /* Written data value is too low  (ABCC40) */
                       ABP_ERR_CONTROLLED_FROM_OTHER_CHANNEL = 0x13, # /* NAK writes to "read process data" mapped attr. (ABCC40) */
                       ABP_ERR_MSG_CHANNEL_TOO_SMALL = 0x14,  # /* Response does not fit (ABCC40)   */
                       ABP_ERR_GENERAL_ERROR       = 0x15,    # /* General error (ABCC40)           */
                       ABP_ERR_PROTECTED_ACCESS    = 0x16,    # /* Protected access (ABCC40)        */
                       ABP_ERR_DATA_NOT_AVAILABLE  = 0x17,    # /* Data not available (ABCC40)      */
                       ABP_ERR_OBJ_SPECIFIC        = 0xFF     # /* Object specific error            */
                    )
