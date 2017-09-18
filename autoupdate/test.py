#!/usr/bin/env python
#-*- coding:UTF-8 -*-
import getopt
import sys

def usage():
    str = '''
    \t-h, --help\t\t Print the help info
    \t-u, --url\t\t Set the url of yum repo <EXAMPLE>( -u file:///root/CGS-Linux-MAIN.V4.05-x86_64.dvd.iso )
                                                     ( -u http://127.0.0.1/media/cdrom/)
                                                     ( -u ftp://127.0.0.1/media/cdrom/)
    \t-n, --not\t\t Do not update package <EXAMPLE>( -n kernel,httpd,openssh )
    \t-d, --dvd\t\t Use dvd as yum source
    '''
    print(str)

try:
    options,args = getopt.getopt(sys.argv[1:], "hp:i:n:", ["help", "ip=", "port=","not="])
    for i,j in options:
        if i in ("-h","--help"):
            usage()
        if i in ("-i","--ip"):
            print("ip is %s" % j)
        if i in ("-p","--port"):
            print("port is %s" % j)
        if i in ("-n","--not"):
            for rpm in j.split(','):
                print("not update is %s" % rpm)
except:
    usage()