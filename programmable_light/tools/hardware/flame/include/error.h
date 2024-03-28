/*	The MetroLib library is a suite of functions that provide 
 *	direct communication with a 3D Metrology (-3DM) board over 
 *	USB and RS-232 serial connections.
 *
 *	Copyright (C)2009 Forth Dimension Displays Limited
 *	
 *	This library is free software; you can redistribute it and/or
 *	modify it under the terms of the GNU Lesser General Public
 *	License as published by the Free Software Foundation; either
 *	version 2.1 of the License, or (at your option) any later version.
 *	
 *	This library is distributed in the hope that it will be useful,
 *	but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 *	Lesser General Public License for more details.
 */

#ifndef _ERROR_H
#define _ERROR_H

#define ERR_OPEN_FAILED                 -100
#define ERR_CLOSE_FAILED                -101
#define ERR_READ_FAILED                 -102
#define ERR_WRITE_FAILED                -103
#define ERR_TIMEOUT                     -104
#define ERR_LIB_USB                     -105
#define ERR_USB_CONFIG_FAILED           -106
#define ERR_USB_CLAIM_FAILED            -107

#define ERR_DEVICE_NOT_FOUND            -200
#define ERR_DEVICE_ALREADY_OPEN         -201
#define ERR_NO_DEVICE_OPEN              -202
#define ERR_INVALID_DEVICE_TYPE         -203
#define ERR_NO_RS232_DEVICE_OPEN        -204
#define ERR_SET_BAUDRATE_FAILED         -205
#define ERR_SET_TIMEOUT_FAILED          -206

#define ERR_INVALID_PACKET_TYPE         -300

#define ERR_MEM_ALLOC_FAILED            -400
#define ERR_NULL_POINTER                -401
#define ERR_INDEX_OUT_OF_BOUNDS         -402

#define ERR_BOARD_EXCEPTION             -500
#define ERR_BOARD_ERROR                 -501

#endif
