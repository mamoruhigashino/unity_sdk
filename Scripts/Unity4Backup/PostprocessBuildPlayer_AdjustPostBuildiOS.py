#!/usr/bin/env python

import sys
import re
from subprocess import Popen, PIPE
import argparse

from mod_pbxproj import XcodeProject

def main():
    parser = argparse.ArgumentParser(description="Adjust post build iOS script")
    parser.add_argument('ios_project_path', help="path to the folder of the iOS project generated by unity3d")
    
    with open('AdjustPostBuildiOSLog.txt', 'w') as fileLog:
        # Log function with file injected.
        LogFunc = LogInput(fileLog)
       
        # Path of the Xcode SDK on the system.
        xcode_sdk_path = get_xcode_sdk_path(LogFunc)

        # Path for unity iOS Xcode project and framework on the system.
        unity_xcode_project_path, framework_path = get_paths(LogFunc, parser, xcode_sdk_path)

        # Edit the Xcode project using mod_pbxproj:
        #  - Add the adSupport framework library.
        #  - Add the iAd framework library.
        #  - Change the compilation flags of the adjust project files to support non-ARC.
        edit_unity_xcode_project(LogFunc, unity_xcode_project_path, framework_path)

        # Removed.
        # Change the Xcode project directly:
        #  - Allow objective-c exceptions
        # rewrite_unity_xcode_project(LogFunc, unity_xcode_project_path)
    sys.exit(0)

def LogInput(writeObject):
    def Log(message, *args):
        messageNLine = (message if message else "None") + "\n"
        writeObject.write(messageNLine.format(*args))
    return Log

def get_paths(Log, parser, xcode_sdk_path):
    args, ignored_args = parser.parse_known_args()
    ios_project_path = args.ios_project_path

    unity_xcode_project_path = ios_project_path + "/Unity-iPhone.xcodeproj/project.pbxproj"
    Log("Unity3d Xcode project path: {0}", unity_xcode_project_path)

    framework_path = xcode_sdk_path + "/System/Library/Frameworks/"
    Log("Framework path: {0}", framework_path)

    return unity_xcode_project_path, framework_path

def edit_unity_xcode_project(Log, unity_xcode_project_path, framework_path):
    # load unity iOS pbxproj project file
    unity_XcodeProject = XcodeProject.Load(unity_xcode_project_path)
    
    # Add AdSupport.framework to unity if it's not already there
    Log("Adding AdSupport.framework to Xcode project.")
    unity_XcodeProject.add_file_if_doesnt_exist(framework_path + "AdSupport.framework", tree="SDKROOT", create_build_files=True,weak=True)
    Log("AdSupport.framework successfully added.")

    # Add iAd.framework to unity if it's not already there
    Log("Adding iAd.framework to Xcode project.")
    unity_XcodeProject.add_file_if_doesnt_exist(framework_path + "iAd.framework", tree="SDKROOT", create_build_files=True,weak=True)
    Log("iAd.framework successfully added.")

    # Add CoreTelephony.framework to unity if it's not already there
    Log("Adding CoreTelephony.framework to Xcode project.")
    unity_XcodeProject.add_file_if_doesnt_exist(framework_path + "CoreTelephony.framework", tree="SDKROOT", create_build_files=True,weak=True)
    Log("CoreTelephony.framework successfully added.")

    # Removed.
    # Don't do anything with ARC at the moment.
    #
    # regex for adjust sdk files
    # re_adjust_files = re.compile(r"AI.*\.m|.*\+AI.*\.m|Adjust\.m|AdjustUnity\.mm")
    # 
    # 
    # Iterate all objects in the unity Xcode iOS project file
    # for key in unity_XcodeProject.get_ids():
    #     obj = unity_XcodeProject.get_obj(key)
    #     
    #     name = obj.get('name')
    #     isa = obj.get('isa')
    #     path = obj.get('path')
    #     fileref = obj.get('fileRef')
    # 
    #     #Log("key: {0}, name: {1}, isa: {2}, path: {3}, fileref: {4}", key, name, isa, path, fileref)
    # 
    #     #check if file reference match any adjust file
    #     adjust_file_match = re_adjust_files.match(name if name else "")
    #     if (adjust_file_match):
    #         #Log("file match, group: {0}", adjust_file_match.group())
    #         # get the build file, from the file reference id
    #         build_files = unity_XcodeProject.get_build_files(key)
    #         for build_file in build_files:
    #             # add the ARC compiler flag to the adjust file if doesn't exist
    #             build_file.add_compiler_flag('-fobjc-arc')
    #             Log("added ARC flag to file {0}", name)

    # Add -ObjC to "Other Linker Flags" project settings.
    Log("Adding -ObjC to other linker flags.")
    unity_XcodeProject.add_other_ldflags('-ObjC')
    Log("Flag -ObjC successfully added.")

    # Save changes.
    unity_XcodeProject.save()

def rewrite_unity_xcode_project(Log, unity_xcode_project_path):
    unity_xcode_lines = []
    
    # Allow objective-c exceptions
    re_objc_excep = re.compile(r"\s*GCC_ENABLE_OBJC_EXCEPTIONS *= *NO.*")
    with open(unity_xcode_project_path) as upf:
        for line in upf:
            if re_objc_excep.match(line):
                Log("Enabling Objective-C exceptions in Xcode project.")
                line = line.replace("NO","YES")
                Log("Objective-C exceptions successfully enabled.")
            unity_xcode_lines.append(line)
    with open(unity_xcode_project_path, "w+") as upf:
        upf.writelines(unity_xcode_lines)

def get_xcode_sdk_path(Log):
    # Output all info from Xcode.
    proc = Popen(["xcodebuild", "-version", "-sdk"], stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    
    if proc.returncode not in [0, 66]:
        Log("Could not retrieve Xcode SDK path.")
        Log("code: {0}, err: {1}", proc.returncode, err)
        return None

    match = re.search("iPhoneOS.*?Path: (?P<sdk_path>.*?)\n", out, re.DOTALL)
    xcode_sdk_path = match.group('sdk_path') if match else None
    
    Log("Xcode SDK path: {0}", xcode_sdk_path)
    
    return xcode_sdk_path

if __name__ == "__main__":
    main()
