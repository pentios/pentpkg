'''
Copyright 2021 Mason Meirs

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions 
of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH 
THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import sys
import os
import requests
import tarfile
import shutil
from distutils.dir_util import copy_tree
import platform
import subprocess

#globals
package_list_dir = "/etc/pentpkg/packages/"
sources_path = "/etc/pentpkg/sources"
tmp = "/tmp/"
package_file_ext = ".ptg"
arch = platform.machine()
kernel = os.uname().sysname
def install(force, *packages):
    for p in packages:
        fsources = open(sources_path,'r')
        sources = fsources.readlines()
        #check if the package exists
        if(os.path.exists(package_list_dir+str(p[0]))):
            if not force:
                print("package already installed: "+ p[0])
                continue
            else:
                print("reinstalling "+ p[0])
        for s in sources:
            #check if the source has the package
            print("downloading "+str(p[0]))
            request = requests.get(str(s)+"/"+str(p[0])+package_file_ext)
            if request.status_code==200:
                open(tmp+str(p[0])+".ptg",'wb').write(request.content)
                tar = tarfile.open(tmp+str(p[0])+package_file_ext, "r:gz")
                tar.extractall(tmp+str(p[0]))
                tar.close()
                fdeps = open(tmp+str(p[0])+"/DEPS",'r')
                finfo = open(tmp+str(p[0])+"/PKGINFO",'r')
                deps = fdeps.readlines()
                info = finfo.readlines()
                for i in info:
                    val = i.split()
                    if val[0] == "arch":
                        if val[1] != arch:
                            print("package not compatible with this system!")
                            break
                    if val[0] == "kernel":
                        if val[1] != kernel:
                            print("package uses a different kernel!")
                            break
                #install dependencies
                for d in deps:
                    install(str(d))
                shutil.copyfile(tmp+str(p[0])+"/PKGTREE", package_list_dir+str(p[0]))
                copy_tree(tmp+str(p[0]), "/")
                if os.path.exists(tmp+str(p[0])+"/POSTINST"):
                    print("running post-install script")
                    subprocess.call(['sh',tmp+str(p[0])+"/POSTINST"])
                print("installed "+str(p[0]))
                fdeps.close()
                break
            else:
                #source doesn't have package
                print(s+" does not provide "+str(p[0]))
        fsources.close()
        print("cleaning up")
        if(os.path.exists(tmp+str(p[0])+package_file_ext)):
            os.remove(tmp+str(p[0])+package_file_ext)
            shutil.rmtree(tmp+str(p[0]))
        print("done")

def installlocal(*packages):
    if(os.path.exists(str(packages[0][0]))):
        tar = tarfile.open(str(packages[0][0]), "r:gz")
        tar.extractall(tmp+str(packages[0][0]))
        tar.close()
        fdeps = open(tmp+str(packages[0][0])+"/DEPS",'r')
        deps = fdeps.readlines()
        finfo = open(tmp+str(packages[0][0])+"/PKGINFO",'r')
        info = finfo.readlines()
        for i in info:
            val = i.split()
            if val[0] == "arch":
                if val[1] != arch:
                    print("package not compatible with this system!")
                    break
            if val[0] == "kernel":
                if val[1] != os.uname().sysname():
                    print("package uses a different kernel!")
                    break
        #install dependencies
        for d in deps:
            install(str(d))
        shutil.copyfile(tmp+str(packages[0][0])+"/PKGTREE", package_list_dir+str(packages[0][0].replace(".ptg", "")))
        copy_tree(tmp+str(packages[0][0]), "/")
        print("installed "+str(packages[0][0]))
        fdeps.close()
        print("cleaning up")
        shutil.rmtree(tmp+str(packages[0][0]))
        print("done")
    else:
        print("not found")
        
def remove(*packages):
    for p in packages:
        #if it's installed
        if(os.path.exists(package_list_dir+str(p[0]))):
            ffiles = open(package_list_dir+str(p[0]),'r')
            files = ffiles.readlines()
            for f in files:
                if(os.path.exists(str(f))):
                    #delete its entry in the package library
                    os.remove(str(f))
            os.remove(package_list_dir+str(p[0]))
    print("removed "+str(p[0]))
    print("done")
 
def add_source(source):
    #append source to sources file
    fsources = open(sources_path, "a")
    fsources.write("\n")
    fsources.write(source)
    fsources.close()

def upgrade():
    install(os.listdir(True, package_list_dir))

def print_usage():
    print("pentpkg <command> {<packages>|<source>}")
    print(" commands:")
    print("     install - installs <packages>")
    print("     local-install - installs <filename of package>")
    print("     remove - removes <packages>")
    print("     add-source - adds <source> to source list")
    print("     upgrade - upgrades all packages.")
    print(" info:")
    print("     pentpkg is a drop-in package manager for any system.")
    print("     originally written for pentios linux.")
    print("     written by Mason Meirs in 2021.")
    
if(len(sys.argv)>1):
    if(sys.argv[1]=="install"):
        sys.argv.pop(0) 
        sys.argv.pop(0) 
        install(False, sys.argv)
    elif(sys.argv[1]=="install-local"):
        sys.argv.pop(0) 
        sys.argv.pop(0) 
        installlocal(sys.argv)
    elif(sys.argv[1]=="remove"):
        sys.argv.pop(0) 
        sys.argv.pop(0) 
        remove(sys.argv)
    elif(sys.argv[1]=="add-source"):
        sys.argv.pop(0) 
        sys.argv.pop(0) 
        add_source(sys.argv[2])
    elif(sys.argv[1]=="upgrade"):
        upgrade()
    else:
        print_usage()
else:
    print_usage()



