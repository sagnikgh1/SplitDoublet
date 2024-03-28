# -*- coding: utf-8 -*-

#--------------------------------------------------------------------#
#                                                                    #
# Copyright (C) 2018 HOLOEYE Photonics AG. All rights reserved.      #
# Contact: https://holoeye.com/contact/                              #
#                                                                    #
# This file is part of HOLOEYE SLM Display SDK.                      #
#                                                                    #
# You may use this file under the terms and conditions of the        #
# "HOLOEYE SLM Display SDK Standard License v1.0" license agreement. #
#                                                                    #
#--------------------------------------------------------------------#


#--------------------------------------------------------------------#
#                                                                    #
# Copyright (C) 2018 HOLOEYE Photonics AG. All rights reserved.      #
# Contact: https://holoeye.com/contact/                              #
#                                                                    #
# This file is part of HOLOEYE SLM Display SDK.                      #
#                                                                    #
# You may use this file under the terms and conditions of the        #
# "HOLOEYE SLM Display SDK Standard License v1.0" license agreement. #
#                                                                    #
#--------------------------------------------------------------------#


# Please import this file in your scripts before actually importing the HOLOEYE SLM Display SDK,
# i. e. copy this file to your project and use this code in your scripts:
#
# import detect_heds_module_path
# import holoeye
#
#
# Another option is to copy the holoeye module directory into your project and import by only using
# import holoeye
# This way, code completion etc. might work better.


import os, sys

# Import the SLM Display SDK:
HEDSModulePath = os.getenv("HEDS_PYTHON_MODULES", "")
print("HEDSModulePath = " + HEDSModulePath)
if HEDSModulePath == "":
    print('\033[91m' + "\nError: Could not find HOLOEYE SLM Display SDK installation path from environment variable. \n\nPlease relogin your Windows user account and try again. \nIf that does not help, please reinstall the SDK and then relogin your user account and try again. \nA simple restart of the computer might fix the problem, too." + '\033[0m')
    if input("\nDo you want to restart the computer now? \nType YES and press Enter to restart, or press Enter to cancel:\n") == "YES":
        print("Restarting system ...\n")
        os.system("shutdown.exe -r -t 0 -f")
    sys.exit(1)
sys.path.append(HEDSModulePath)