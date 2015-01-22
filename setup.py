#!/usr/bin/env python 
# -*- coding: utf-8 -*-

# Copyright (C) 2010 Modelon AB  
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#from distutils.core import setup, Extension
import numpy as N
import logging as L
import sys as S
import os
import shutil as SH
import ctypes.util
import argparse

try:
    from Cython.Distutils import build_ext
    from Cython.Build import cythonize
except ImportError:
    raise Exception("Please upgrade to a newer Cython version, >= 0.15.")

#L.basicConfig(format='%(levelname)s:%(message)s')

incdirs = ''
libdirs = ''
python3_flag = True if sys.hexversion > 0x03000000 else False

thirdparty_methods=["hairer","voigtmann", "hindmarsh","odassl","dasp3"]

try:
    from subprocess import Popen, PIPE
    _p = Popen(["svnversion", "."], stdout=PIPE)
    revision = _p.communicate()[0].decode('ascii')
except:
    revision = "unknown"

if 'win' in sys.platform:
    incdirs = ''
    libdirs = ''
else:
    incdirs = '/usr/local/include'
    libdirs = '/usr/local/lib'

static_link_gcc = ["-static-libgcc"]
static_link_gfortran = ["-static-libgfortran"]
flag_32bit = ["-m32"]

force_32bit = False
no_msvcr = False
extra_c_flags = ''

parser = argparse.ArgumentParser()
parser.add_argument("--plugins-home", help="Location of the Assimulo plugin irectory")
parser.add_argument("--sundials-home", help="Location of the SUNDIALS directory")
parser.add_argument("--superlu-home'", help="Location of the SuperLU directory")
parser.add_argument("--lapack-home", help="Location of the LAPACK directory")
parser.add_argument("--blas-home", help="Location of the BLAS directory")
parser.add_argument("--blas-name", help="name of the blas package")   
parser.add_argument("--extra-c-flags", help='Extra C-flags (a list enclosed in " ")')                  
parser.add_argument("--is_static", action="store_true", help="set to true if present")
parser.add_argument("--debug", action="store_true", help="set to true if present")
parser.add_argument("--force-32bit", action="store_true", help="set to true if present")
parser.add_argument("--no-msvcr", action="store_true", help="set to true if present")

                                       
args = parser.parse_known_args()

if args.sundials_home:
	incdirs = os.path.join(args.sundials_home,'include')
    libdirs = os.path.join(args.sundials_home,'lib')
SLUdir = args.superlu_home or ''
BLASdir = args.blas_home or ''
BLASname_t = args.blas_name or ''
debug_flag = args.debug or False
LAPACKdir = args.lapack_home or ''
PLUGINSdir = args.plugins_home or ''
static = args.is_static or False
debug = args.debug or False
force_32bit = args.force_32bit or False
no_mvscr = args.no_msvcr or False
extra_c_flags = args.extra_c_flags or ''

copy_args=sys.argv[1:]

for x in sys.argv[1:]:
    if not x.find('--prefix'):
        copy_args[copy_args.index(x)] = x.replace('/',os.sep)
    if not x.find('--log'):
        level = x[6:]
        try:
            num_level = getattr(L, level.upper())
        except AttributeError:
            L.warning("No log-level defined for: "+level)
            num_level = 30
        L.basicConfig(level=num_level)
        copy_args.remove(x)

def check_platform():
    platform = None
    if sys.platform == 'win32':
        platform = "win"
    elif sys.platform == 'darwin':
        platform = "mac"
    else:
        platform = "linux"
    return platform

def pre_processing():
    join = os.path.join
    def create_dir(d):
        try:
            os.makedirs(d) #Create the build directory
        except OSError:
            pass #Directory already exists
    build_assimulo=os.path.join("build","assimulo")
    build_assimulo_thirdparty=os.path.join(build_assimulo,'thirdparty')
    for subdir in ["lib," "solvers", "examples"]:
        create_dir(os.path.join(build_assimulo,subdir))
    create_dir(os.path.join(build_assimulo,"tests","solvers"))
    for package in thirdparty_methods:
        create_dir(join(build_assimulo_thirdparty,package))
    
    fileSrc     = os.listdir("src")
    fileLib     = os.listdir(os.path.join("src","lib"))
    fileSolvers = os.listdir(os.path.join("src","solvers"))
    fileExamples= os.listdir("examples")
    fileMain    = ["setup.py","README","INSTALL","CHANGELOG","MANIFEST.in"]
    fileTests   = os.listdir("tests")
    
    filelist_thirdparty=dict([(thp,os.listdir(join("thirdparty",thp))) 
                                         for thp in thirdparty_methods])
    
    fileTestsSolvers = os.listdir(os.path.join("tests","solvers"))
    
    
    curdir = os.path.dirname(os.path.abspath(__file__))
    
    desSrc = os.path.join(curdir,build_assimulo)
    desLib = os.path.join(desSrc,"lib"))
    desSolvers = os.path.join(desSrc,"solvers")
    desExamples = os.path.join(desSrc,"examples")
    desMain = os.path.join(curdir,"build")
    desTests = os.path.join(desSrc,"tests")
    desTestsSolvers = os.path.join(desTests,"solvers")
    
    desThirdparty=dict([(thp,os.path.join(curdir,build_assimulo_thirdparty,thp)) 
                                          for thp in thirdparty_methods])
    

    for f in fileSrc:
        if not os.path.isdir(os.path.join("src",f)):
            SH.copy2(os.path.join("src",f), desSrc)
    for f in fileLib:
        if not os.path.isdir(os.path.join(os.path.join("src","lib"),f)):
            SH.copy2(os.path.join(os.path.join("src","lib"),f), desLib)
    for f in fileSolvers:
        if not os.path.isdir(os.path.join(os.path.join("src","solvers"),f)):
            SH.copy2(os.path.join(os.path.join("src","solvers"),f), desSolvers)
    for f in fileExamples:
        if not os.path.isdir(os.path.join("examples",f)):
            SH.copy2(os.path.join("examples",f), desExamples)
    for f in fileMain:
        if not os.path.isdir(f):
            SH.copy2(f,desMain)
    for f in fileTests:
        if not os.path.isdir(os.path.join("tests",f)):
            SH.copy2(os.path.join("tests",f), desTests)
    for f in fileTestsSolvers:
        if not os.path.isdir(os.path.join("tests","solvers",f)):
            SH.copy2(os.path.join("tests","solvers",f),desTestsSolvers)
            
    for solver in thirdparty_methods:
		for f in filelist_thirdparty.items():
			if not os.path.isdir(join("thirdparty",f[0],f[1])):
                 SH.copy2(os.path.join("thirdparty",f[0],f[1]),desThirdParty[f[0]])
        if f[1] == "LICENSE_{}".f[0].upper():   ## needs to be fixed for "hindmarsh"
            SH.copy2(join("thirdparty",f[0],f[1]),desLib)

            
    #Delete OLD renamed files
    delFiles = [("lib","sundials_kinsol_core_wSLU.pxd")]
    for item in delFiles:
        dirDel = desSrc
        for f in item[:-1]:
            dirDel = os.path.join(dirDel, f)
        dirDel = os.path.join(dirDel, item[-1])
        if os.path.exists(dirDel):
            try:
                os.remove(dirDel)
            except:
                L.warning("Could not remove: "+str(dirDel))

if no_msvcr:
    # prevent the MSVCR* being added to the DLLs passed to the linker
    def msvc_runtime_library_mod(): 
        return None

    import numpy.distutils
    numpy.distutils.misc_util.msvc_runtime_library = msvc_runtime_library_mod

def check_extensions():
    extra_link_flags = []
    
    if static:
        extra_link_flags += static_link_gcc
    if force_32bit:
        extra_link_flags += flag_32bit
    
    #Cythonize main modules
    ext_list = cythonize(["assimulo"+os.path.sep+"*.pyx"], include_path=[".","assimulo"],include_dirs=[N.get_include()],pyrex_gdb=debug_flag)
    
    #Cythonize Euler
    ext_list = ext_list + cythonize(["assimulo"+os.path.sep+"solvers"+os.path.sep+"euler.pyx"], include_path=[".","assimulo"],include_dirs=[N.get_include()],pyrex_gdb=debug_flag)
    
    for i in ext_list:
        i.include_dirs = [N.get_include()]
            
    #If Sundials
    if os.path.exists(os.path.join(os.path.join(incdirs,'cvodes'), 'cvodes.h')):
        #CVode and IDA
        ext_list = ext_list + cythonize(["assimulo"+os.path.sep+"solvers"+os.path.sep+"sundials.pyx"], include_path=[".","assimulo","assimulo"+os.sep+"lib"],include_dirs=[N.get_include()],pyrex_gdb=debug_flag)
        ext_list[-1].include_dirs = [N.get_include(), "assimulo","assimulo"+os.sep+"lib", incdirs]
        ext_list[-1].library_dirs = [libdirs]
        ext_list[-1].libraries = ["sundials_cvodes", "sundials_nvecserial", "sundials_idas"]
        
        #Kinsol
        ext_list = ext_list + cythonize(["assimulo"+os.path.sep+"solvers"+os.path.sep+"kinsol.pyx"], include_path=[".","assimulo","assimulo"+os.sep+"lib"],include_dirs=[N.get_include()],pyrex_gdb=debug_flag)
        ext_list[-1].include_dirs = [N.get_include(), "assimulo","assimulo"+os.sep+"lib", incdirs]
        ext_list[-1].library_dirs = [libdirs]
        ext_list[-1].libraries = ["sundials_kinsol", "sundials_nvecserial"]
    else:
        L.warning("Could not find Sundials, check the provided path (--sundials-home) to see that it actually points to Sundials.")
        L.warning("Could not find cvodes.h in " + os.path.join(incdirs,'cvodes'))

        
    for i in ext_list:
        #Debug
        if debug_flag:
            i.extra_compile_args = ["-g","-fno-strict-aliasing"]
            i.extra_link_args = ["-g"]
        else:
            i.extra_compile_args = ["-O2", "-fno-strict-aliasing"]
        if check_platform() == "mac":
            i.extra_compile_args += ["-Wno-error=return-type"]
        if force_32bit:
            i.extra_compile_args += flag_32bit
        if extra_c_flags:
            flags = extra_c_flags.split(' ')
            for f in flags:
                i.extra_compile_args.append(f)
    
    #Sundials found
    if os.path.exists(os.path.join(os.path.join(incdirs,'cvodes'), 'cvodes.h')):
        cordir = os.path.join(os.path.join('assimulo','lib'),'sundials_core.pyx')
        cordir_KINSOL_wSLU = os.path.join(os.path.join('assimulo','lib'),'sundials_kinsol_core_wSLU.pyx')
        cordir_KINSOL = os.path.join(os.path.join('assimulo','lib'),'sundials_kinsol_core.pyx')
    
        cordir_KINSOL_jmod_wSLU = os.path.join(os.path.join('assimulo','lib'),'kinsol_jmod_wSLU.c')
        cordir_KINSOL_jmod = os.path.join(os.path.join('assimulo','lib'),'kinsol_jmod.c')
    
        cordir_kinpinv = os.path.join(os.path.join('assimulo','lib'),'kinpinv.c')
        cordir_kinslug = os.path.join(os.path.join('assimulo','lib'),'kinslug.c')
        cordir_reg_routines = os.path.join(os.path.join('assimulo','lib'),'reg_routines.c')

        
        wSLU = check_wSLU()
        if wSLU:
            SLUincdir = os.path.join(SLUdir,'SRC')
            SLUlibdir = os.path.join(SLUdir,'lib')
            #ext_list = ext_list + [Extension('assimulo.lib.sundials_kinsol_core_wSLU',
            #              [cordir_KINSOL_wSLU,cordir_KINSOL_jmod_wSLU,cordir_kinpinv,cordir_kinslug,cordir_reg_routines],
            #              include_dirs=[incdirs, N.get_include(),SLUincdir],
            #              library_dirs=[libdirs,SLUlibdir,BLASdir],
            #              libraries=['sundials_kinsol','sundials_nvecserial','superlu_4.1',BLASname])]
            ext_list = ext_list + cythonize([cordir_KINSOL_wSLU], include_path=[".","assimulo","assimulo"+os.sep+"lib"])
            ext_list[-1].sources += [cordir_KINSOL_jmod_wSLU,cordir_kinpinv,cordir_kinslug,cordir_reg_routines]
            ext_list[-1].include_dirs = [N.get_include(), SLUincdir, incdirs]
            ext_list[-1].library_dirs = [libdirs,SLUlibdir,BLASdir]
            ext_list[-1].libraries = ["sundials_kinsol", "sundials_nvecserial", "superlu_4.1",BLASname,'gfortran']
            if debug_flag:
                ext_list[-1].extra_compile_args = ["-g", "-fno-strict-aliasing"]
            else:
                ext_list[-1].extra_compile_args = ["-O2", "-fno-strict-aliasing"]
            if check_platform() == "mac":
                ext_list[-1].extra_compile_args += ["-Wno-error=return-type"]
            if force_32bit:
                ext_list[-1].extra_compile_args += flag_32bit
            if extra_c_flags:
                flags = extra_c_flags.split(' ')
                for f in flags:
                    ext_list[-1].extra_compile_args.append(f)
                
        else:
            #ext_list = ext_list + [Extension('assimulo.lib.sundials_kinsol_core',
            #              [cordir_KINSOL,cordir_KINSOL_jmod,cordir_kinpinv],
            #              include_dirs=[incdirs, N.get_include()],
            #              library_dirs=[libdirs],
            #              libraries=['sundials_kinsol','sundials_nvecserial'])]

            ext_list = ext_list + cythonize([cordir_KINSOL])#, include_path=[".","assimulo","assimulo"+os.sep+"lib"])
            ext_list[-1].sources += [cordir_KINSOL_jmod,cordir_kinpinv]
            ext_list[-1].include_dirs = [N.get_include(), incdirs]
            ext_list[-1].library_dirs = [libdirs]
            ext_list[-1].libraries = ["sundials_kinsol", "sundials_nvecserial"]
            if debug_flag:
                ext_list[-1].extra_compile_args = ["-g", "-fno-strict-aliasing"]
            else:
                ext_list[-1].extra_compile_args = ["-O2", "-fno-strict-aliasing"]
            if check_platform() == "mac":
                ext_list[-1].extra_compile_args += ["-Wno-error=return-type"]
            if force_32bit:
                ext_list[-1].extra_compile_args += flag_32bit
            if extra_c_flags:
                flags = extra_c_flags.split(' ')
                for f in flags:
                    ext_list[i].extra_compile_args.append(f)
    
    for i in ext_list:
        if python3_flag:
            i.cython_directives = {"language_level": 3}
        i.extra_link_args += extra_link_flags
    
    return ext_list

def check_wSLU():
    wSLU = True
    
    global BLASname, BLASname_t
    
    if SLUdir != "":    
        SLUincdir = os.path.join(SLUdir,'SRC')
        SLUlibdir = os.path.join(SLUdir,'lib')
        if not os.path.exists(os.path.join(SLUincdir,'supermatrix.h')):
            wSLU = False
            L.warning("Could not find SuperLU, disabling support. View more information using --log=DEBUG")
            L.debug("Could not find SuperLU at the given path.")
            L.debug("usage: --superlu-home=path")
            L.debug("KINSOL will not be compiled with support for SUperLU.")
            
        L.debug("SLUinc: "+SLUincdir)
        L.debug("SLUlib: "+SLUlibdir)

    else:
        L.warning("No path to SuperLU supplied, disabling support. View more information using --log=DEBUG")
        L.debug("No path to SuperLU supplied, KINSOL will not be compiled with support for SUperLU.")
        L.debug("usage: --superlu-home=path")
        L.debug("Note: the path required is to the folder where the folders 'SRC' and 'lib' are found.")
        wSLU = False
        
    if BLASname_t != "":
        if BLASname_t.startswith("lib"):
            BLASname = BLASname_t[3:]
        else:
            BLASname = BLASname_t
            BLASname_t = "lib"+BLASname_t
    else:
        BLASname_t = "lib" + BLASname
           
    if BLASdir == "":
        L.warning("No path to BLAS supplied, disabling support. View more information using --log=DEBUG")
        L.debug("No path to BLAS supplied, KINSOL will not be compiled with support for SUperLU.")
        L.debug("usage: --blas-home=path")
        L.debug("Note: the path required is to where the static library lib"+BLASname+" is found")
        wSLU = False
    else:
        if not os.path.exists(os.path.join(BLASdir,BLASname_t+'.a')):
            L.warning("Could not find BLAS, disabling support. View more information using --log=DEBUG")
            L.debug("Could not find BLAS at the given path.")
            L.debug("usage: --blas-home=path")
            L.debug("KINSOL will not be compiled with support for SUperLU.")
            wSLU = False
            
        L.debug("BLAS: "+BLASdir+"/"+BLASname_t)
    
    return wSLU


def check_fortran_extensions():
    """
    Adds the Fortran extensions using Numpy's distutils extension.
    """
    extra_link_flags = []
    extra_compile_flags = []
    if static:
        extra_link_flags += static_link_gfortran + static_link_gcc
    if force_32bit:
        extra_link_flags += flag_32bit
        extra_compile_flags += flag_32bit
    if extra_c_flags:
        flags = extra_c_flags.split(' ')
        for f in flags:
            extra_compile_flags.append(f)
    
    from numpy.distutils.misc_util import Configuration
    config = Configuration()

    if force_32bit:
        config.add_extension('assimulo.lib.dopri5',
                             sources=['assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'dopri5.f','assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'dopri5.pyf']
                             ,extra_link_args=extra_link_flags[:],extra_compile_args=extra_compile_flags[:], extra_f77_compile_args=extra_compile_flags[:])#include_dirs=[N.get_include()])
        
        config.add_extension('assimulo.lib.rodas',
                             sources=['assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'rodas_decsol.f','assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'rodas_decsol.pyf'],
                             include_dirs=[N.get_include()],extra_link_args=extra_link_flags[:],extra_compile_args=extra_compile_flags[:], extra_f77_compile_args=extra_compile_flags[:])
        
        config.add_extension('assimulo.lib.radau5',
                             sources=['assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'radau_decsol.f','assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'radau_decsol.pyf'],
                             include_dirs=[N.get_include()],extra_link_args=extra_link_flags[:],extra_compile_args=extra_compile_flags[:], extra_f77_compile_args=extra_compile_flags[:])
    
        config.add_extension('assimulo.lib.radar5',
                             sources=['assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'contr5.f90',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'radar5_int.f90',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'radar5.f90',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'dontr5.f90',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'decsol.f90',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'dc_decdel.f90',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'radar5.pyf'],
                             include_dirs=[N.get_include()],extra_link_args=extra_link_flags[:],extra_compile_args=extra_compile_flags[:], extra_f77_compile_args=extra_compile_flags[:],extra_f90_compile_args=extra_compile_flags[:])#, extra_f90_compile_args=["-O2"])#, extra_f77_compile_args=['-O2']) # extra_compile_args=['--noopt'])
        
        #ODEPACK
        config.add_extension('assimulo.lib.odepack',
                             sources=['assimulo'+os.sep+'thirdparty'+os.sep+'hindmarsh'+os.sep+'opkdmain.f',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hindmarsh'+os.sep+'opkda1.f',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hindmarsh'+os.sep+'opkda2.f',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hindmarsh'+os.sep+'odepack_aux.f90',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hindmarsh'+os.sep+'odepack.pyf'],
                             include_dirs=[N.get_include()],extra_link_args=extra_link_flags[:],extra_compile_args=extra_compile_flags[:], extra_f77_compile_args=extra_compile_flags[:],extra_f90_compile_args=extra_compile_flags[:])
        
        #ODASSL
        odassl_dir='assimulo'+os.sep+'thirdparty'+os.sep+'odassl'+os.sep
        odassl_files=['odassl.pyf','odassl.f','odastp.f','odacor.f','odajac.f','d1mach.f','daxpy.f','ddanrm.f','ddatrp.f','ddot.f',
                      'ddwats.f','dgefa.f','dgesl.f','dscal.f','idamax.f','xerrwv.f']
        config.add_extension('assimulo.lib.odassl',
                             sources=[odassl_dir+file for file in odassl_files],
                             include_dirs=[N.get_include()],extra_link_args=extra_link_flags[:],extra_compile_args=extra_compile_flags[:], extra_f77_compile_args=extra_compile_flags[:],extra_f90_compile_args=extra_compile_flags[:])
    else:
        config.add_extension('assimulo.lib.dopri5',
                             sources=['assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'dopri5.f','assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'dopri5.pyf']
                             ,extra_link_args=extra_link_flags[:])#include_dirs=[N.get_include()])
        
        config.add_extension('assimulo.lib.rodas',
                             sources=['assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'rodas_decsol.f','assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'rodas_decsol.pyf'],
                             include_dirs=[N.get_include()],extra_link_args=extra_link_flags[:])
        
        config.add_extension('assimulo.lib.radau5',
                             sources=['assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'radau_decsol.f','assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'radau_decsol.pyf'],
                             include_dirs=[N.get_include()],extra_link_args=extra_link_flags[:])
    
        config.add_extension('assimulo.lib.radar5',
                             sources=['assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'contr5.f90',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'radar5_int.f90',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'radar5.f90',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'dontr5.f90',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'decsol.f90',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'dc_decdel.f90',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hairer'+os.sep+'radar5.pyf'],
                             include_dirs=[N.get_include()],extra_link_args=extra_link_flags[:])#, extra_f90_compile_args=["-O2"])#, extra_f77_compile_args=['-O2']) # extra_compile_args=['--noopt'])
        
        #ODEPACK
        config.add_extension('assimulo.lib.odepack',
                             sources=['assimulo'+os.sep+'thirdparty'+os.sep+'hindmarsh'+os.sep+'opkdmain.f',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hindmarsh'+os.sep+'opkda1.f',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hindmarsh'+os.sep+'opkda2.f',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hindmarsh'+os.sep+'odepack_aux.f90',
                                      'assimulo'+os.sep+'thirdparty'+os.sep+'hindmarsh'+os.sep+'odepack.pyf'],
                             include_dirs=[N.get_include()],extra_link_args=extra_link_flags[:])
        
        #ODASSL
        odassl_dir='assimulo'+os.sep+'thirdparty'+os.sep+'odassl'+os.sep
        odassl_files=['odassl.pyf','odassl.f','odastp.f','odacor.f','odajac.f','d1mach.f','daxpy.f','ddanrm.f','ddatrp.f','ddot.f',
                      'ddwats.f','dgefa.f','dgesl.f','dscal.f','idamax.f','xerrwv.f']
        config.add_extension('assimulo.lib.odassl',
                             sources=[odassl_dir+file for file in odassl_files],
                             include_dirs=[N.get_include()],extra_link_args=extra_link_flags[:])
        
    #DASP3
    dasp3_f77_compile_flags = ["-fdefault-double-8","-fdefault-real-8"]
    if force_32bit:
        dasp3_f77_compile_flags += flag_32bit
    
    if N.version.version > "1.6.1": #NOTE, THERE IS A PROBLEM WITH PASSING F77 COMPILER ARGS FOR NUMPY LESS THAN 1.6.1, DISABLE FOR NOW
        dasp3_dir='assimulo'+os.sep+'thirdparty'+os.sep+'dasp3'+os.sep
        dasp3_files = ['dasp3dp.pyf', 'DASP3.f', 'ANORM.f','CTRACT.f','DECOMP.f',
                       'HMAX.f','INIVAL.f','JACEST.f','PDERIV.f','PREPOL.f','SOLVE.f','SPAPAT.f']
        config.add_extension('assimulo.lib.dasp3dp',
                              sources=[dasp3_dir+file for file in dasp3_files],
                              include_dirs=[N.get_include()],extra_link_args=extra_link_flags[:],extra_f77_compile_args=dasp3_f77_compile_flags[:],extra_compile_args=extra_compile_flags[:],extra_f90_compile_args=extra_compile_flags[:])
    else:
        L.warning("DASP3 requires a numpy > 1.6.1. Disabling...")

    
    #GLIMDA
    #ADD liblapack and libblas
    lapack = False
    blas = False
    if LAPACKdir != "":
        lapack = True
        extra_link_flags += ["-L"+LAPACKdir, "-llapack"]
    else: #Try to see if Lapack exists in PATH
        name = ctypes.util.find_library("lapack")
        if name != None:
            extra_link_flags += ["-l"+name.split(os.path.sep)[-1].replace("lib","").split(".")[0]]
            lapack = True
    if BLASdir != "":
        blas = True
        extra_link_flags += ["-L"+BLASdir, "-lblas"]
    else: #Try to see if Blas exists in PATH
        name = ctypes.util.find_library("blas")
        if name != None:
            extra_link_flags += ["-l"+name.split(os.path.sep)[-1].replace("lib","").split(".")[0]]
            blas = True
    
    if lapack and blas:
        if force_32bit:
            config.add_extension('assimulo.lib.glimda',
                             sources=['assimulo'+os.sep+'thirdparty'+os.sep+'voigtmann'+os.sep+'glimda_complete.f','assimulo'+os.sep+'thirdparty'+os.sep+'voigtmann'+os.sep+'glimda_complete.pyf'],
                             include_dirs=[N.get_include()],extra_link_args=extra_link_flags[:],extra_compile_args=extra_compile_flags[:], extra_f77_compile_args=extra_compile_flags[:],extra_f90_compile_args=extra_compile_flags[:])
        else:
            config.add_extension('assimulo.lib.glimda',
                             sources=['assimulo'+os.sep+'thirdparty'+os.sep+'voigtmann'+os.sep+'glimda_complete.f','assimulo'+os.sep+'thirdparty'+os.sep+'voigtmann'+os.sep+'glimda_complete.pyf'],
                             include_dirs=[N.get_include()],extra_link_args=extra_link_flags[:])

    else:
        L.warning("Could not find Blas or Lapack, disabling support for the solver GLIMDA.")
    

    return config.todict()["ext_modules"]

"""
Pre-processing is necessary due to the setup of the repository. 
"""
if not os.path.isdir("assimulo"):
    pre_processing()
    os.chdir("build") #Change dir
    change_dir = True
else:
    change_dir = False
      
ext_list = check_extensions()

#MAJOR HACK DUE TO NUMPY CHANGE IN VERSION 1.6.2 THAT DOES NOT SEEM TO
#HANDLE EXTENSIONS OF BOTH TYPE (DISTUTILS AND NUMPY DISTUTILS) AT THE
#SAME TIME.
for e in ext_list:
    e.extra_f77_compile_args = []
    e.extra_f90_compile_args = []

ext_list += check_fortran_extensions()


NAME = "Assimulo"
AUTHOR = "C. Andersson, C. Führer, J. Åkesson, M. Gäfvert"
AUTHOR_EMAIL = "chria@maths.lth.se"
VERSION = "trunk"
LICENSE = "LGPL"
URL = "http://www.jmodelica.org/assimulo"
DOWNLOAD_URL = "http://www.jmodelica.org/assimulo"
DESCRIPTION = "A package for solving ordinary differential equations and differential algebraic equations."
PLATFORMS = ["Linux", "Windows", "MacOS X"]
CLASSIFIERS = [ 'Programming Language :: Python',
                'Programming Language :: Cython',
                'Programming Language :: C',
                'Programming Language :: Fortran',
                'Operating System :: MacOS :: MacOS X',
                'Operating System :: Microsoft :: Windows',
                'Operating System :: Unix']

LONG_DESCRIPTION = """
Assimulo is a Cython / Python based simulation package that allows for 
simulation of both ordinary differential equations (ODEs), f(t,y), and 
differential algebraic equations (DAEs), f(t,y,yd). It combines a 
variety of different solvers written in C, FORTRAN and Python via a 
common high-level interface.

Assimulo currently supports Explicit Euler, adaptive Runge-Kutta of 
order 4 and Runge-Kutta of order 4. It also wraps the popular SUNDIALS 
(https://computation.llnl.gov/casc/sundials/main.html) solvers CVode 
(for ODEs) and IDA (for DAEs). Ernst Hairer's 
(http://www.unige.ch/~hairer/software.html) codes Radau5, Rodas and 
Dopri5 are also available.

Documentation and installation instructions can be found at: 
http://www.jmodelica.org/assimulo . 

For questions and comments, visit: 
http://www.jmodelica.org/forums/jmodelicaorg-platform/assimulo

The package requires Numpy, Scipy and Matplotlib and additionally for 
compiling from source, Cython 0.15, Sundials 2.4/2.5, BLAS and LAPACK 
together with a C-compiler and a FORTRAN-compiler.
"""


version_txt = 'assimulo'+os.path.sep+'version.txt'
#If a revision is found, always write it!
if revision != "unknown" and revision!="":
    with open(version_txt, 'w') as f:
        f.write(VERSION+'\n')
        f.write("r"+revision)
else:# If it does not, check if the file exists and if not, create the file!
    if not os.path.isfile(version_txt):
        with open(version_txt, 'w') as f:
            f.write(VERSION+'\n')
            f.write("unknown")

from numpy.distutils.core import setup
setup(name=NAME,
      version=VERSION,
      license=LICENSE,
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      download_url=DOWNLOAD_URL,
      platforms=PLATFORMS,
      classifiers=CLASSIFIERS,
      package_dir = {'assimulo':'assimulo'},
      packages=['assimulo', 'assimulo.lib','assimulo.solvers','assimulo.examples','assimulo.tests','assimulo.tests.solvers'],
      #cmdclass = {'build_ext': build_ext},
      ext_modules = ext_list,
      package_data={'assimulo': ['version.txt',
                                 'thirdparty'+os.sep+'hairer'+os.sep+'LICENSE_HAIRER','lib'+os.sep+'LICENSE_HAIRER',
                                 'thirdparty'+os.sep+'voigtmann'+os.sep+'LICENSE_GLIMDA','lib'+os.sep+'LICENSE_GLIMDA',
                                 'thirdparty'+os.sep+'hindmarsh'+os.sep+'LICENSE_ODEPACK','lib'+os.sep+'LICENSE_ODEPACK',
                                 'thirdparty'+os.sep+'odassl'+os.sep+'LICENSE_ODASSL','lib'+os.sep+'LICENSE_ODASSL',
                                 'thirdparty'+os.sep+'dasp3'+os.sep+'LICENSE_DASP3','lib'+os.sep+'LICENSE_DASP3',
                                 'examples'+os.sep+'kinsol_ors_matrix.mtx','examples'+os.sep+'kinsol_ors_matrix.mtx']},
      script_args=copy_args)

if change_dir:
    os.chdir("..") #Change back to dir
