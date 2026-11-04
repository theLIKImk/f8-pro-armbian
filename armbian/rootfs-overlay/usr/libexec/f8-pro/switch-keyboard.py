#!/usr/bin/python3
import subprocess,sys,time
mode=sys.argv[1] if len(sys.argv)>1 else 'fcitx5'
choices={'fcitx5':'fyi.fortime.Fcitx5Osk.KwinLauncher.desktop','plasma':'org.kde.plasma.keyboard.desktop'}
if mode not in choices:raise SystemExit('Choose fcitx5 or plasma')
subprocess.run(['kwriteconfig6','--notify','--file','kwinrc','--group','Wayland','--key','InputMethod','/usr/share/applications/'+choices[mode]],check=True)
subprocess.run(['kwriteconfig6','--notify','--file','kwinrc','--group','Wayland','--key','VirtualKeyboardEnabled','true'],check=True)
subprocess.run(['qdbus6','org.kde.KWin','/KWin','reconfigure'],check=True)
if mode=='plasma':
 service='fyi.fortime.Fcitx5Osk'
 owned=subprocess.run(['qdbus6','org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus.NameHasOwner',service],capture_output=True,text=True).stdout.strip()
 if owned=='true':subprocess.run(['qdbus6',service,'/fyi/fortime/Fcitx5Osk/Controller','fyi.fortime.Fcitx5Osk.Controller1.Shutdown'],check=False)

