#!/usr/bin/python3 -I
"""Retire only the fixed R1 setup account after the new Wayland login works."""
import argparse,json,os,pwd,re,stat,subprocess,time
from pathlib import Path

SETUP='f8setup'
SETUP_UID=1601

def decision(state):
    if not state['complete']:return 'pending-first-run'
    if not state['new_user_valid']:return 'pending-valid-new-user'
    if not state['new_wayland_active']:return 'pending-new-desktop-login'
    if not state['setup_exists']:return 'already-retired'
    if not state['setup_identity_valid']:raise ValueError('临时账户身份与R1配置不符，未执行清理。')
    if not state['setup_disabled']:raise ValueError('临时账户未被禁用，未执行清理。')
    if state['setup_processes']:return 'pending-setup-session-exit'
    return 'retire'

def retire(root,name,run=subprocess.run):
    home=root/'home/f8setup';archive=root/'var/lib/f8-pro/retired-setup-r1'
    if home.is_symlink() or home.resolve()!=home:raise ValueError('临时家目录路径异常，未执行清理。')
    if archive.is_symlink():raise ValueError('备份路径异常。')
    archive.mkdir(mode=0o700,parents=True,exist_ok=True);archive.chmod(0o700)
    if archive.stat().st_uid!=0:raise ValueError('备份目录归属异常。')
    saved=archive/'home'
    if saved.exists() or saved.is_symlink():raise ValueError('备份目录已存在，未覆盖。')
    moved=False
    if home.exists():
        if not home.is_dir() or home.stat().st_dev!=archive.stat().st_dev:raise ValueError('临时家目录不是同一文件系统内的普通目录。')
        home.rename(saved);moved=True
    try:
        # No -r and no forced termination: userdel also refuses a busy account.
        run(['/usr/sbin/userdel',SETUP],check=True,capture_output=True,timeout=30)
    except Exception:
        if moved and not home.exists():saved.rename(home)
        raise ValueError('账户清理未完成，目录已恢复；请先退出临时账户会话。') from None
    rule=root/'etc/sudoers.d/f8-first-run'
    expected='f8setup ALL=(root) NOPASSWD: /usr/local/lib/f8-pro/first-run-apply.py ""'
    if rule.is_file() and not rule.is_symlink() and rule.read_text().strip()==expected:rule.unlink()
    cache=root/'var/lib/AccountsService/users/f8setup'
    if cache.is_file() and not cache.is_symlink():cache.rename(archive/'accounts-service-settings')
    record={'ok':True,'removed_account':SETUP,'new_user':name,'home_preserved_at':str(saved) if moved else None,'time':time.time()}
    (archive/'complete.json').write_text(json.dumps(record,indent=2)+'\n')
    return record

def stop_timer():
    subprocess.run(['systemctl','disable','--now','f8-setup-cleanup.timer'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    if os.geteuid()!=0:raise ValueError('请在新账户登录后用sudo运行；不需要提供密码给其他人。')
    if not Path('/etc/f8-pro-release-r1').is_file():raise ValueError('只支持本项目R1系统。')
    marker=Path('/var/lib/f8-pro/first-run/complete.json')
    if not marker.is_file():print(json.dumps({'action':'pending-first-run'}));return
    if marker.is_symlink() or marker.stat().st_uid!=0:raise ValueError('首次设置记录归属异常。')
    name=json.loads(marker.read_text())['username']
    if not re.fullmatch(r'[a-z][a-z0-9_-]{0,30}',name) or name in {'root',SETUP}:raise ValueError('新账户记录异常。')
    account=pwd.getpwnam(name)
    valid=account.pw_uid>=1000 and account.pw_uid!=SETUP_UID and account.pw_shell not in {'/bin/false','/sbin/nologin','/usr/sbin/nologin'}
    sessions=subprocess.check_output(['loginctl','list-sessions','--no-legend','--no-pager'],text=True,timeout=10).splitlines()
    active=False
    for row in sessions:
        fields=row.split()
        if not fields:continue
        text=subprocess.check_output(['loginctl','show-session',fields[0],'-p','User','-p','Type','-p','Active','-p','Class'],text=True,timeout=10)
        props=dict(x.split('=',1) for x in text.splitlines() if '=' in x)
        if props.get('User')==str(account.pw_uid) and props.get('Type')=='wayland' and props.get('Active')=='yes' and props.get('Class')=='user':active=True
    try:old=pwd.getpwnam(SETUP)
    except KeyError:old=None
    disabled=False
    if old:
        shadow=next((x.split(':') for x in Path('/etc/shadow').read_text().splitlines() if x.startswith(SETUP+':')),None)
        disabled=bool(shadow and shadow[1].startswith(('!','*')) and shadow[7] and int(shadow[7])<=int(time.time()//86400))
    processes=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            ids=next(x.split()[1:] for x in (p/'status').read_text().splitlines() if x.startswith('Uid:'))
            if str(SETUP_UID) in ids:processes.append(int(p.name))
        except (OSError,StopIteration):continue
    state=dict(complete=True,new_user_valid=valid,new_wayland_active=active,setup_exists=old is not None,setup_identity_valid=old is not None and old.pw_uid==SETUP_UID and old.pw_dir=='/home/f8setup' and old.pw_shell=='/usr/sbin/nologin',setup_disabled=disabled,setup_processes=processes)
    action=decision(state)
    if not args.apply or action!='retire':
        if args.apply and action=='already-retired':stop_timer()
        print(json.dumps({'action':action,'applied':False},ensure_ascii=True));return
    record=retire(Path('/'),name)
    stop_timer()
    print(json.dumps(record,ensure_ascii=True))

if __name__=='__main__':
    try:main()
    except (ValueError,KeyError) as e:raise SystemExit(str(e))
