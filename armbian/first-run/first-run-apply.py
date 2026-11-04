#!/usr/bin/python3 -I
"""Single-use account setup helper. Passwords enter through stdin only."""
import fcntl
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import subprocess
import sys

LOCALES={'zh_CN.UTF-8','en_US.UTF-8','zh_TW.UTF-8'}

def validate(data, root=Path('/')):
    if set(data)!={'username','fullname','password','locale','timezone','hostname','autologin'}:
        raise ValueError('向导数据不完整，请重新提交。')
    name=data['username']
    if not isinstance(name,str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,30}',name) or name in {'root','f8setup','f8test','f8gpu'}:
        raise ValueError('用户名须以小写字母开头，只含小写字母、数字、下划线或短横线。')
    password=data['password']
    if not isinstance(password,str) or not 8<=len(password)<=128 or any(ord(c)<32 or ord(c)==127 or c==':' for c in password):
        raise ValueError('密码须为8至128个字符，不能包含冒号或控制字符。')
    full=data['fullname']
    if not isinstance(full,str) or len(full)>80 or any(ord(c)<32 or c in ':,' for c in full):
        raise ValueError('显示名称无效。')
    if data['locale'] not in LOCALES or type(data['autologin']) is not bool:
        raise ValueError('语言或登录选项无效。')
    host=data['hostname']
    if not isinstance(host,str) or not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',host):
        raise ValueError('设备名只能包含小写字母、数字和短横线。')
    tz=data['timezone']
    if not isinstance(tz,str) or not re.fullmatch(r'[A-Za-z0-9_+/-]{1,100}',tz) or '..' in tz.split('/'):
        raise ValueError('时区无效。')
    base=(root/'usr/share/zoneinfo').resolve()
    zone=(base/tz).resolve()
    if not zone.is_relative_to(base) or not zone.is_file() or not zone.read_bytes().startswith(b'TZif'):
        raise ValueError('系统中没有这个时区。')
    accounts=(root/'etc/passwd').read_text().splitlines()
    if any(x.split(':')[0]==name for x in accounts):
        raise ValueError('该用户名已存在，请选择其他名字。')
    home=root/'home'/name
    if home.exists() or home.is_symlink():
        raise ValueError('这个用户名对应的家目录已存在，请选择其他名字。')
    return data

def write(root,name,text,mode=0o644):
    p=root/name.lstrip('/');p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_name(p.name+'.f8-new')
    with temp.open('w',encoding='utf-8') as f:
        os.fchmod(f.fileno(),mode);f.write(text);f.flush();os.fsync(f.fileno())
    os.replace(temp,p)

def apply(data,root=Path('/'),run=subprocess.run):
    marker=root/'var/lib/f8-pro/first-run/complete.json'
    if marker.exists():raise ValueError('首次设置已经完成。')
    if not (root/'etc/f8-pro-release-r1').is_file():raise ValueError('当前系统没有启用首次设置。')
    validate(data,root)
    name=data['username'];created=False;stage='准备'
    def command(args,**kw):
        # Never propagate chpasswd stderr or supplied secrets to GUI/log output.
        return run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=45,**kw)
    try:
        stage='生成语言环境';locale=data['locale'];stem=locale.split('.')[0]
        command(['/usr/bin/localedef','-i',stem,'-f','UTF-8',locale])
        stage='创建用户'
        command(['/usr/sbin/useradd','-M','-U','-s','/bin/bash','-c',data['fullname'],'-G','sudo,video,render,audio,netdev',name])
        created=True
        home=root/'home'/name
        # useradd -M deliberately leaves the home absent: copy links exactly once.
        stage='安装桌面默认配置'
        shutil.copytree(root/'etc/skel',home,symlinks=True)
        home.chmod(0o750)
        stage='设置账户密码'
        command(['/usr/sbin/chpasswd'],input=(name+':'+data['password']+'\n').encode())
        # Defaults in /etc/skel are installed before useradd.
        stage='保存语言和时区';config=home/'.config';config.mkdir(parents=True,exist_ok=True)
        write(root,f'home/{name}/.config/plasma-localerc',f'[Formats]\nLANG={locale}\n[Translations]\nLANGUAGE={stem}\n')
        write(root,'etc/default/locale',f'LANG={locale}\nLANGUAGE={stem}\n')
        write(root,'etc/hostname',data['hostname']+'\n')
        write(root,'etc/hosts',f'127.0.0.1 localhost\n127.0.1.1 {data["hostname"]}\n::1 localhost ip6-localhost ip6-loopback\n')
        zone=root/'etc/localtime';zone.unlink(missing_ok=True);zone.symlink_to('/usr/share/zoneinfo/'+data['timezone'])
        write(root,'etc/timezone',data['timezone']+'\n')
        stage='设置家目录权限';command(['/usr/bin/chown','-R',name+':'+name,'/home/'+name])
        auto=f'User={name}\nSession=plasma.desktop\nRelogin=false\n' if data['autologin'] else 'User=\nSession=plasma.desktop\nRelogin=false\n'
        write(root,'etc/sddm.conf.d/99-f8-first-run.conf','[Autologin]\n'+auto)
        # Disable setup login; do not remove the running setup user's home/session.
        stage='关闭临时设置账户';command(['/usr/sbin/usermod','-L','-e','1','-s','/usr/sbin/nologin','f8setup'])
        stage='写入完成记录'
        write(root,'var/lib/f8-pro/first-run/complete.json',json.dumps({'version':1,'username':name,'locale':locale,'timezone':data['timezone'],'autologin':data['autologin']})+'\n',0o600)
    except Exception as error:
        if not marker.exists():
            # Keep a recoverable setup login. Delete only the account created here.
            write(root,'etc/sddm.conf.d/99-f8-first-run.conf','[Autologin]\nUser=f8setup\nSession=plasma.desktop\nRelogin=false\n')
            run(['/usr/sbin/usermod','-e','','-s','/bin/bash','f8setup'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30)
            if created:
                run(['/usr/sbin/userdel','-r',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30)
        # Show the operation and error type, never command stdin/stderr or password.
        detail=type(error).__name__
        if isinstance(error,subprocess.CalledProcessError):detail+=' exit='+str(error.returncode)
        raise ValueError('设置未完成：'+stage+'（'+detail+'）。已保留向导入口，请保留此提示。') from None
    return {'ok':True,'username':name}

def main():
    os.umask(0o077)
    if os.geteuid()!=0 or os.environ.get('SUDO_USER')!='f8setup' or len(sys.argv)!=1:
        raise ValueError('请从首次开机向导提交设置。')
    lock=Path('/run/f8-first-run.lock').open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    raw=sys.stdin.buffer.read(8193)
    if len(raw)>8192:raise ValueError('提交内容过长。')
    data=json.loads(raw)
    if not isinstance(data,dict):raise ValueError('设置格式无效。')
    print(json.dumps(apply(data)))

if __name__=='__main__':
    try:main()
    except ValueError as e:
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));sys.exit(1)
    except Exception:
        print(json.dumps({'ok':False,'error':'设置未完成，已保留向导入口。请重试；若仍失败，请保留当前界面。'},ensure_ascii=False));sys.exit(1)
