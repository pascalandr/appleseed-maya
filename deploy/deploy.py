#!/usr/bin/python

#
# This source file is part of appleseed.
# Visit http://appleseedhq.net/ for additional information and resources.
#
# This software is released under the MIT license.
#
# Copyright (c) 2017 Esteban Tovagliari, The appleseedhq Organization
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import sys
import os
import shutil
import glob
import argparse
import platform
from distutils.dir_util import copy_tree

def get_maya_version(build_dir):
    maya_include_dir = None

    # Find the Maya include dir from CMake's cache.
    f = open(os.path.join(build_dir, 'CMakeCache.txt'), 'r')
    lines = f.readlines()
    f.close()

    token = 'MAYA_INCLUDE_DIR:PATH=/usr/autodesk/maya2017/include'
    for line in lines:
        if line.startswith(token):
            maya_include_dir = line.split('=')[1].strip()
            break

    # Find the Maya version from Maya's MTypes.h header.
    f = open(os.path.join(maya_include_dir, 'maya', 'MTypes.h'), 'r')
    lines = f.readlines()
    f.close()

    for line in lines:
        if '#define' in line:
            if 'MAYA_API_VERSION' in line:
                tokens = line.split()
                return tokens[-1][:4]

def get_appleseed_maya_version():
    this_dir = os.path.dirname(os.path.realpath(__file__))
    src_dir = os.path.join(this_dir, '..', 'src', 'appleseedmaya')

    # Find the Maya include dir from CMake's cache.
    f = open(os.path.join(src_dir, 'version.h'), 'r')
    lines = f.readlines()
    f.close()

    major = -1
    minor = -1
    patch = -1

    for line in lines:
        if line.startswith('#define APPLESEED_MAYA_VERSION_'):
            tokens = line.split()
            if tokens[1] == 'APPLESEED_MAYA_VERSION_MAJOR':
                major = int(tokens[2])
            elif tokens[1] == 'APPLESEED_MAYA_VERSION_MINOR':
                minor = int(tokens[2])
            elif tokens[1] == 'APPLESEED_MAYA_VERSION_PATCH':
                patch = int(tokens[2])

    return (major, minor, patch)

def copy_plugins(args):
    if platform.system().lower() == 'linux':
        plugin_ext = '.so'
    elif platform.system().lower() == 'windows':
        plugin_ext = '.mll'
    else:
        print 'Error: Unsupported platform'
        sys.exit(0)

    plugins_dir = os.path.join(args.directory, 'plug-ins')
    if not os.path.exists(plugins_dir):
        os.makedirs(plugins_dir)

    print 'Copying appleseedMaya plugin'
    shutil.copy(
        os.path.join(args.build_dir, 'src', 'appleseedmaya', 'appleseedMaya' + plugin_ext),
        plugins_dir
    )

def generate_module_file(args, maya_version, major_version, minor_version, patch_version):
    f = open(os.path.join(args.directory, 'appleseedMaya.mod'), 'w')
    f.write('+ appleseedMaya any .\n')

    f.write('PATH +:= bin\n')

    if platform.system().lower() == 'linux':
        f.write('LD_LIBRARY_PATH +:= lib\n')

    f.write('\n')

    f.write('PYTHONPATH +:= scripts\n')
    f.write('\n')

    f.write('APPLESEED_SEARCHPATH := shaders\n')
    f.close()

def copy_appleseed(args):
    bin_dir = os.path.join(args.directory, 'bin')
    if not os.path.exists(bin_dir):
        os.makedirs(bin_dir)

    binaries_to_copy = [
        'appleseed.cli',
        'maketx'
    ]
    for bin in binaries_to_copy:
        shutil.copy(os.path.join(args.appleseed_dir, 'bin', bin), bin_dir)

    if platform.system().lower() == 'linux':
        lib_dir = os.path.join(args.directory, 'lib')
        if not os.path.exists(lib_dir):
            os.makedirs(lib_dir)

        libraries_to_copy = [
            'libboost_atomic-gcc48-mt-1_55.so.1.55.0',
            'libboost_chrono-gcc48-mt-1_55.so.1.55.0',
            'libboost_date_time-gcc48-mt-1_55.so.1.55.0',
            'libboost_filesystem-gcc48-mt-1_55.so.1.55.0',
            'libboost_python-gcc48-mt-1_55.so.1.55.0',
            'libboost_regex-gcc48-mt-1_55.so.1.55.0',
            'libboost_serialization-gcc48-mt-1_55.so.1.55.0',
            'libboost_system-gcc48-mt-1_55.so.1.55.0',
            'libboost_thread-gcc48-mt-1_55.so.1.55.0',
            'libboost_wave-gcc48-mt-1_55.so.1.55.0',

            'libz.so.1',
            'libxerces-c-3.1.so',

            'libHalf.so.12',
            'libIex-2_2.so.12',
            'libIlmThread-2_2.so.12',
            'libImath-2_2.so.12',

            'libIlmImf-2_2.so.22',

            'libjpeg.so.62',
            'libpng16.so.16',
            'libtiff.so.3',

            'libOpenImageIO.so.1.7',

            'libSeExpr.so',

            'libLLVM-3.4.so',
            'liboslcomp.so',
            'liboslexec.so',
            'liboslquery.so',

            'libappleseed.so',
            'libappleseed.shared.so'
        ]
        for lib in libraries_to_copy:
            shutil.copy(os.path.join(args.appleseed_dir, 'lib', lib), lib_dir)

    # Copy python module.
    copy_tree(os.path.join(args.appleseed_dir, 'lib', 'python2.7'), os.path.join(args.directory, 'scripts'))

    # Copy shaders.
    shaders_dir = os.path.join(args.directory, 'shaders')
    if not os.path.exists(shaders_dir):
        os.makedirs(shaders_dir)

    for shader in glob.glob(os.path.join(args.appleseed_dir, 'shaders', 'maya', '*.oso')):
        shutil.copy(shader, shaders_dir)

    for shader in glob.glob(os.path.join(args.appleseed_dir, 'shaders', 'appleseed', '*.oso')):
        shutil.copy(shader, shaders_dir)

    # Copy schemas and settings.
    dirs_to_copy = ['schemas', 'settings']
    for dir in dirs_to_copy:
        copy_tree(os.path.join(args.appleseed_dir, dir), os.path.join(args.directory, dir))

def main():
    parser = argparse.ArgumentParser(description='Deploy Maya plugin')

    parser.add_argument('-b', '--build-dir', metavar='build-dir', help='set the path to the build directory')
    parser.add_argument('-a', '--appleseed-dir', metavar='appleseed-dir', help='set the path to the appleseed directory')
    parser.add_argument('directory', help='destination directory')
    args = parser.parse_args()

    (major_version, minor_version, patch_version) = get_appleseed_maya_version()
    print 'Deploying appleseedMaya %s.%s.%s to %s...' % (
        major_version,
        minor_version,
        patch_version,
        args.directory
        )
    this_dir = os.path.dirname(os.path.realpath(__file__))
    root_dir = os.path.join(this_dir, '..')

    print 'Creating deploy directory...'
    if not os.path.exists(args.directory):
        os.makedirs(args.directory)

    maya_version = get_maya_version(args.build_dir)
    print 'Maya version = %s' % maya_version

    print 'Copying module file...'
    generate_module_file(args, maya_version, major_version, minor_version, patch_version)

    print 'Copying icons...'
    copy_tree(os.path.join(root_dir, 'icons'), os.path.join(args.directory, 'icons'))

    print 'Copying presets...'
    copy_tree(os.path.join(root_dir, 'presets'), os.path.join(args.directory, 'presets'))

    print 'Copying resources...'
    copy_tree(os.path.join(root_dir, 'resources'), os.path.join(args.directory, 'resources'))

    print 'Copying scripts...'
    copy_tree(os.path.join(root_dir, 'scripts'), os.path.join(args.directory, 'scripts'))

    print 'Copying license...'
    shutil.copy(os.path.join(this_dir, '..', 'LICENSE.txt'), args.directory)

    print 'Copying plugins...'
    copy_plugins(args)

    if args.appleseed_dir:
        print 'Copying appleseed binaries and libraries...'
        copy_appleseed(args)

if __name__ == '__main__':
    main()
