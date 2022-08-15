#-*- encoding:UTF-8 -*-
__author__ = 'wuyou'
import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import paramiko
import time
from PrintInfo import Print
from stat import S_ISDIR
from time import sleep
import socket

class SSH(object):
    def __init__(self, ip_address, username, password):
        self.__ip = ip_address
        self.__username = username
        self.__password = password
        self.__init_ssh_client()

    def __init_ssh_client(self):
        try:
            self.__ssh_client = paramiko.SSHClient()
            self.__ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.__ssh_client.connect(self.__ip, username=self.__username, password=self.__password, timeout=4)
        except socket.timeout:
            print 'SSH CONNECT TIME OUT'
            os.system('netsh wlan connect MTBF_APQ8096')
            sleep(60)
            self.__init_ssh_client()

    def pull_file(self, remote_path, local_path):
        scp_client = self.__get_scp_client()
        sftp = paramiko.SFTPClient.from_transport(scp_client)
        list_dict_all_files = self.__get_all_files_in_remote_dir(sftp=sftp, remote_path=remote_path, local_path=local_path)
        for dict_file in list_dict_all_files:
            sftp.get(remotepath=dict_file.get('remote'), localpath=dict_file.get('local'))
        sftp.close()
        scp_client.close()

    def push_file(self, local_path, remote_path):
        scp_client = self.__get_scp_client()
        sftp = paramiko.SFTPClient.from_transport(scp_client)
        # 去掉路径字符穿最后的字符'/'，如果有的话
        if remote_path[-1] == '/':
            remote_path = remote_path[0:-1]
        # 获取本地指定目录及其子目录下的所有文件
        list_dict_all_files = self.__get_all_files_in_local_dir(local_path, remote_path)
        # 依次put每一个文件
        for dict_file in list_dict_all_files:
            sftp.put(localpath=dict_file.get('local'), remotepath=dict_file.get('remote'))
        sftp.close()
        scp_client.close()

    def get_ssh_client(self):
        return self.__ssh_client

    def __get_scp_client(self):
        try:
            scp_client = paramiko.Transport((self.__ip, 22))
            scp_client.connect(username=self.__username, password=self.__password)
            return scp_client
        except Exception, e:
            os.system('netsh wlan connect MTBF_APQ8096')
            Print.error(e)
            time.sleep(3)
            return self.__get_scp_client()

    def close_ssh_client(self):
        self.__ssh_client.close()

    def ssh_connect_to_host(self):
        try:
            self.__ssh_client.connect(self.__ip, username=self.__username, password=self.__password, timeout=4)
        except Exception, e:
            Print.error(e)
            time.sleep(5)
            self.ssh_connect_to_host()

    def scp_connect_to_host(self):
        try:
            self.__scp_client.connect(username=self.__username, password=self.__password)
        except Exception, e:
            Print.error(e)
            time.sleep(5)
            self.scp_connect_to_host()

    def exec_command(self, command):
        try:
            # stdin, stdout, stderr =
            return self.__ssh_client.exec_command(command)
        except Exception, e:
            Print.error(e)
            self.ssh_connect_to_host()
            return self.exec_command(command)

    #    ------获取远端linux主机上指定目录及其子目录下的所有文件------
    def __get_all_files_in_remote_dir(self, sftp, remote_path, local_path):
        # 去掉路径字符串最后的字符'/'，如果有的话
        if remote_path[-1] == '/':
            remote_path = remote_path[0:-1]
        if S_ISDIR(sftp.stat(remote_path).st_mode):
            # 保存所有文件的列表
            all_files = list()
            files = sftp.listdir_attr(remote_path)
            for x in files:
                # remote_dir目录中每一个文件或目录的完整路径
                filename = remote_path + '/' + x.filename
                # 如果是目录，则递归处理该目录，这里用到了stat库中的S_ISDIR方法，与linux中的宏的名字完全一致
                if S_ISDIR(x.st_mode):
                    all_files.extend(self.__get_all_files_in_remote_dir(sftp=sftp,
                                                                        remote_path=filename,
                                                                        local_path=os.path.join(local_path, x.filename)))
                    try:
                        os.makedirs(os.path.join(local_path, x.filename))
                    except WindowsError:
                        pass
                else:
                    dict_file = dict()
                    dict_file['local'] = os.path.join(local_path, x.filename)
                    dict_file['remote'] = filename
                    all_files.append(dict_file)
            return all_files
        else:
            dict_file = dict()
            dict_file['local'] = local_path
            dict_file['remote'] = remote_path
            return [dict_file]



    # ------获取本地指定目录及其子目录下的所有文件------
    def __get_all_files_in_local_dir(self, local_path, remote_path):
        if os.path.isdir(local_path):
            self.__ssh_client.exec_command('mkdir -p %s' % remote_path)
            sleep(1)
            all_files = list()
            # 保存所有文件的列表
            # 获取当前指定目录下的所有目录及文件，包含属性值
            files = os.listdir(local_path)
            for x in files:
                # local_dir目录中每一个文件或目录的完整路径
                filename = os.path.join(local_path, x)
                # 如果是目录，则递归处理该目录
                if os.path.isdir(filename):
                    all_files.extend(self.__get_all_files_in_local_dir(local_path=filename, remote_path=remote_path+'/'+x))
                else:
                    dict_file = dict()
                    dict_file['local'] = filename
                    dict_file['remote'] = remote_path + '/' + x
                    all_files.append(dict_file)
            return all_files
        else:
            tmp_list = os.path.split(remote_path)
            self.__ssh_client.exec_command('mkdir -p %s' % tmp_list[0])
            sleep(1)
            dict_file = dict()
            dict_file['local'] = local_path
            dict_file['remote'] = remote_path
            return [dict_file]



if __name__ == '__main__':
    ssh = SSH(ip_address='192.168.1.1', username='root', password='oelinux123')
    ssh.pull_file(local_path='C:\\1\\tmp', remote_path='/usr/lib/rfsa/adsp/')
    ssh.close_ssh_client()