#!/usr/bin/python3
"""Apply Chinese lunar calendar once to the current user's Plasma clock widgets."""
import json,os,subprocess,sys,time
from pathlib import Path
state=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'f8-pro/lunar-calendar-r1.json'
if state.exists() and '--force' not in sys.argv:raise SystemExit(0)
script=r'''
var result=[];
var containers=panels().concat(desktops());
for (var c=0;c<containers.length;c++) {
 var widgets=containers[c].widgets();
 for (var i=0;i<widgets.length;i++) {
  var w=widgets[i];
  if(w.type!=='org.kde.plasma.digitalclock')continue;
  w.currentConfigGroup=['Appearance'];
  var old=w.readConfig('enabledCalendarPlugins',['holidaysevents']);
  var list=(typeof old==='string')?old.split(','):old;
  var plugins=[];
  for(var k=0;k<list.length;k++)if(String(list[k]).length)plugins.push(String(list[k]));
  if(plugins.indexOf('alternatecalendar')<0)plugins.push('alternatecalendar');
  w.writeConfig('enabledCalendarPlugins',plugins);
  w.reloadConfig();
  result.push({id:w.id,plugins:plugins});
 }
}
print(JSON.stringify({clocks:result}));
'''
last=''
for attempt in range(20):
 try:
  r=subprocess.run(['qdbus6','org.kde.plasmashell','/PlasmaShell','org.kde.PlasmaShell.evaluateScript',script],capture_output=True,text=True,timeout=4)
  if r.returncode:raise RuntimeError(r.stderr.strip())
  lines=[x for x in r.stdout.splitlines() if x.startswith('{')]
  data=json.loads(lines[-1]);assert data['clocks'],'No clock widget is ready'
  subprocess.run(['kwriteconfig6','--notify','--file','plasma_calendar_alternatecalendar','--group','General','--key','calendarSystem','Chinese'],check=True,timeout=5)
  state.parent.mkdir(parents=True,exist_ok=True)
  data.update(calendarSystem='Chinese',version=1);state.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps(data));break
 except Exception as e:
  last=str(e);time.sleep(1)
else:raise SystemExit('Calendar defaults deferred: '+last)
