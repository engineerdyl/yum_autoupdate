#!/usr/bin/env python
#-*- coding:UTF-8 -*-
######################################################################
import os,sys
import ConfigParser  #python2
#import configparser  #python3

def init_value():
    """
        功能描述：初始化程序内部使用参数 
        参数：
            无
        返回：
            无
    """
    global main_dir, work_dir, cdrom_dir, backup_dir, kernel_release

    main_dir = '/tmp'
    work_dir = '%s/.autoupdate' % main_dir
    cdrom_dir = '%s/cdrom' % work_dir
    backup_dir = '%s/backup' % work_dir
    kernel_release = os.uname()[2][7:10]

def set_argvs(config_file):
    """
        功能描述：从配置文件中取值，赋予变量
        参数：
            config_file： 配置文件的绝对路径，命令行第一个参数即为文件路径
        返回：
            无
    """
    cf = ConfigParser.ConfigParser() #python2
    #cf = configparser.ConfigParser() #python3
    cf.read(config_file)

    global url,dvd,iso,UpdatePackage,NotUpdatePackage,pre_command,pre_script
    global post_command,post_script

    url = cf.get("pre", "url")
    dvd = cf.get("pre","dvd")
    iso = cf.get("pre","iso")
    UpdatePackage = cf.get("pre","UpdatePackage")
    NotUpdatePackage = cf.get("pre","NotUpdatePackage")
    pre_command = cf.get("pre", "command")
    pre_script = cf.get("pre","script")

    post_command = cf.get("post", "command")
    post_script = cf.get("post", "script")

def check_argv():
    """
        功能描述：检查参数使用情况，有一些参数不能一起使用 
        参数：
            无
        返回：
            无
     """
    if (dvd != '' and dvd != 'yes'):
        exit('''\033[31mParameter config error: "dvd" can only be set to 'yes'\033[0m''')
    elif not (os.path.islink('/dev/cdrom')):
        exit('''\033[31mCannot detect the DVD\033[0m''')

    if (iso != ''):
        if not (os.path.isfile(iso) and iso.split('.')[-1] == 'iso'):
            exit('''\033[31mError: Invalid iso file\033[0m''')

    if (url != ''):
        if ((url.split('://')[0] != 'http') and (url.split('://')[0] != 'ftp') and (url.split('://')[0] != 'file')):
            exit('''\033[31mParameter config error: This url is not a valid source link\033[0m''')

    if ((dvd=='yes' and iso != '') or (dvd=='yes' and url != '') or (iso != '' and url != '')):
        exit('''\033[31mParameter config error: "dvd" "url" "iso" can not be configured at the same time\033[0m''')

    if (UpdatePackage != '' and NotUpdatePackage != ''):
        exit('''\033[31mParameter config error: "UpdatePackage" and "NotUpdatePackage" can not be configured at the same time\033[0m''')

    if (dvd=='' and iso=='' and url==''):
        exit('''\033[31mParameter config error: "dvd" "url" "iso" ,you must configure one of the parameter to specify yum repo\033[0m''')

    if (UpdatePackage != ''):
        for item in UpdatePackage.split():
            result = os.system('''rpm -qa |grep -i ^%s &>/dev/null''' % item)
            if result != 0:
                exit('''\033[31mParameter config error: Package "%s" is not installed,cannot update this package\033[0m''' % item)

    if (NotUpdatePackage != ''):
        for item in NotUpdatePackage.split():
            result = os.system('''rpm -qa |grep -i ^%s &>/dev/null''' % item)
            if result != 0:
                exit('''\033[31mParameter config error: Package "%s" is not installed,cannot ignore this package\033[0m''' % item)

def destroy():
    """
        功能描述：清理升级时临时产生的数据 
        参数：
            无
        返回：
            无
    """
    cmd = '''
    umount %s 2>/dev/null;
    mv %s/* /etc/yum.repos.d/ 2>/dev/null;
    rm -rf %s 2>/dev/null;
    '''% (cdrom_dir,backup_dir,work_dir)
    os.system(cmd)

def set_yum_repo():
    """
        功能描述：按照参数设置yum源 
        参数：
            无
        返回：
            无
    """
    repo_text = '[base]\nname=CGSL - Media\nbaseurl=file://%s/\ngpgcheck=0\nenabled=1' % cdrom_dir
    source_path = ''

    if(dvd == 'yes'):
        source_path = '/dev/cdrom'
    if(iso):
        source_path = iso

    cmd = '''
    mkdir -p %s &>/dev/null;
    mkdir -p %s &>/dev/null;
    mv /etc/yum.repos.d/* %s &>/dev/null;
    echo '%s' > /etc/yum.repos.d/CGSL-Media.repo 2>/dev/null;
    mount -t iso9660 -o loop %s %s &>/dev/null;
    yum clean all &>/dev/null;
    yum repolist;
    ''' % (cdrom_dir, backup_dir, backup_dir, repo_text, source_path, cdrom_dir)

    if(url):
        repo_text = '[base]\nname=CGSL-Media\nbaseurl=%s\ngpgcheck=0\nenabled=1' % url

        cmd = '''
        mkdir -p %s &>/dev/null;
        mkdir -p %s &>/dev/null;
        mv /etc/yum.repos.d/* %s &>/dev/null;
        echo '%s' > /etc/yum.repos.d/CGSL-Media.repo 2>/dev/null;
        yum clean all &>/dev/null;
        yum repolist;
        ''' % (cdrom_dir, backup_dir,backup_dir, repo_text)

    os.system(cmd)

def pre_update():
    """
        功能描述：升级前操作 
        参数：
            无
        返回：
            无
    """
    if(pre_command):
        os.system(pre_command)

    if(pre_script):
        os.system('/bin/bash %s' % pre_script)

    # 特殊处理，例如处理内核,当升级整个系统或指定升级内核包时做的特殊处理
    #kernel
    if(UpdatePackage== '' and ('kernel' not in NotUpdatePackage)) or ('kernel' in UpdatePackage):
        # 如果当前系统为V4.05或以上，kernel升级需作额外处理，V4.05的内核版本为2.6.32-642.13.1
        if kernel_release >= '642':
            rpm = 'kernel-2.* kernel-devel-2.* kernel-headers-2.* kernel-firmware-2.*'

            cmd = '''
            /bin/cp -f /boot/grub/grub.conf /boot/grub/grub.conf.bak ;
            cd %s ;
            yum install -y yum-utils &>/dev/null ;
            yumdownloader %s ;
            rpm -Uvh %s ;
            ''' % (work_dir, rpm, rpm)

            result = os.system(cmd)
            if result ==0:
                print('\033[32m Kernel update successful!\033[0m')

    #后期可以在后面继续添加额外处理
    #other
    # if (xxx):
    #     pass

def post_update():
    """
        功能描述：升级后操作 
        参数：
            无
        返回：
            无
    """
    if (post_command):
        os.system(post_command)

    if (post_script):
        os.system('/bin/bash %s' % post_script)

    # 特殊处理，例如处理内核,当升级整个系统或指定升级内核包时做的特殊处理
    #kernel
    if (UpdatePackage == '' and ('kernel' not in NotUpdatePackage)) or ('kernel' in UpdatePackage):
        # 如果当前系统为V4.05或以上，kernel升级需作额外处理，V4.05的内核版本为2.6.32-642.13.1
        if kernel_release >= '642':
            cmd = '''
            /bin/mv -f /boot/grub/grub.conf.bak /boot/grub/grub.conf;
            '''
            os.system(cmd)

    # 后期可以在后面继续添加额外处理
    # other
    # if (xxx):
    #     pass

def begin_update():
    # 开始升级某些组件
    if (UpdatePackage):
        result = os.system('yum -y update %s;' % UpdatePackage)
        destroy()
        if result == 0:
            print('\033[32m Update successful!\033[0m')
        else:
            print('\033[31m Update failed!\033[0m')

    # 不升级某些组件
    elif (NotUpdatePackage):
        result = os.system('yum -y update -x %s;' % NotUpdatePackage)
        destroy()
        if result == 0:
            print('\033[32m Update successful!\033[0m')
        else:
            print('\033[31m Update failed!\033[0m')

    # 升级整个系统
    else:
        result = os.system('yum -y update;')
        destroy()
        if result == 0:
            print('\033[32m Update successful!\033[0m')
        else:
            print('\033[31m Update failed!\033[0m')

if __name__ == '__main__':
    init_value()
    set_argvs(sys.argv[1])
    check_argv()
    set_yum_repo()
    pre_update()
    begin_update()
    post_update()
    exit()


