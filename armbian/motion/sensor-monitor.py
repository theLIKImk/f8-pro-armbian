#!/usr/bin/python3
"""F8 sensor viewer: unprivileged sysfs reads, no driver or display configuration writes."""
import argparse,collections,datetime,json,math,os,queue,subprocess,threading,time
from pathlib import Path
from PyQt6.QtCore import Qt,QTimer,QPointF
from PyQt6.QtGui import QColor,QFont,QPainter,QPen,QPainterPath
from PyQt6.QtWidgets import QApplication,QFileDialog,QFrame,QGridLayout,QHBoxLayout,QLabel,QMainWindow,QMessageBox,QPushButton,QScrollArea,QScroller,QTabWidget,QVBoxLayout,QWidget
from sensor_examples import Examples
from sensor_fusion import flat_heading,magnetic_pose
from fusion_view import FusionPanel

COLORS=['#67d8ef','#bc9aff','#ffbf6b']
def read_text(path):
    return path.read_text().strip()

def read_device(device):
    result={'device':str(device),'name':read_text(device/'name'),'raw':{},'scaled':{},'errors':[],
            'mount_matrix':{},'monotonic':time.monotonic(),'time':datetime.datetime.now().astimezone().isoformat()}
    for kind in ['accel','anglvel']:
        values=[];raw=[]
        try:
            scale=float(read_text(device/f'in_{kind}_scale'))
            for axis in 'xyz':raw.append(int(read_text(device/f'in_{kind}_{axis}_raw')))
            values=[n*scale for n in raw]
            result['raw'][kind]=raw;result['scaled'][kind]=values
        except (OSError,ValueError) as e:result['errors'].append(f'{kind}: {e}')
        f=device/f'in_{kind}_mount_matrix'
        if f.exists():
            try:result['mount_matrix'][kind]=read_text(f)
            except OSError:pass
    try:
        f=device/'in_temp_input'
        result['temperature_c']=float(read_text(f))/1000 if f.exists() else (float(read_text(device/'in_temp_raw'))+float(read_text(device/'in_temp_offset')))*float(read_text(device/'in_temp_scale'))/1000
    except (OSError,ValueError):pass
    return result

def example_matrix(device):
    candidates=[]
    try:
        p=subprocess.run(['udevadm','info','--query=property','--path='+str(device)],capture_output=True,text=True,timeout=2)
        candidates += [('udev安装矩阵',line.split('=',1)[1]) for line in p.stdout.splitlines() if line.startswith('ACCEL_MOUNT_MATRIX=')]
    except (OSError,subprocess.TimeoutExpired):pass
    try:candidates.append(('IIO安装矩阵',read_text(device/'in_accel_mount_matrix')))
    except OSError:pass
    for source,text in candidates:
        try:
            m=[[float(v) for v in row.split(',')] for row in text.split(';')]
            assert len(m)==3 and all(len(row)==3 for row in m)
            assert all(abs(sum(m[i][k]*m[j][k] for k in range(3))-(1 if i==j else 0))<1e-6 for i in range(3) for j in range(3))
            det=m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])-m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])+m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0])
            assert abs(det-1)<1e-6
            return m,source
        except (ValueError,AssertionError):pass
    return [[1,0,0],[0,1,0],[0,0,1]],'未取得有效安装矩阵，范例使用原始轴'

def read_magnet(device,accel):
    calibration=None;full=False
    try:
        c=json.loads((Path.home()/'.config/f8-pro/compass-calibration.json').read_text())
        assert c['version'] in [1,2,3] and max(c.get('spans_ut',[0]))<=250
        assert len(c['offset_ut'])==len(c['scale'])==3 and all(math.isfinite(v) for k in ['offset_ut','scale'] for v in c[k]) and all(.1<v<10 for v in c['scale'])
        calibration=c;full=c['version']==2 and 'field_radius_ut' in c
    except (OSError,ValueError,KeyError,TypeError,AssertionError):pass
    meta={'full_3d':full,'calibration_present':calibration is not None,'heading':None}
    try:
        values=[float(read_text(device/f'in_magn_{axis}_raw'))*float(read_text(device/f'in_magn_{axis}_scale'))*100 for axis in 'xyz']
        out={**meta,'measurement_valid':True,'monotonic':time.monotonic(),'raw_ut':values,'field':math.sqrt(sum(v*v for v in values)),'compass_note':'未校准，请打开指南针校准'}
        if calibration:
            corrected=[(values[i]-c['offset_ut'][i])*c['scale'][i] for i in range(3)];out['corrected_ut']=corrected
            flat=accel and accel[2]/max(1e-6,math.sqrt(sum(v*v for v in accel)))<-.92
            if full and accel:
                ab=[sum(row[i]*accel[i] for i in range(3)) for row in ((0,-1,0),(-1,0,0),(0,0,-1))]
                mp=magnetic_pose(ab,corrected)
                if mp:out['heading']=mp['heading'];out['compass_note']='三轴校准 · 倾斜补偿'
                else:out['compass_note']='磁场异常或水平分量不足'
            elif not flat:out['compass_note']='平面校准仅支持屏幕朝上平放'
            elif math.hypot(corrected[0],corrected[1])>200:out['compass_note']='磁场干扰较强，请移开磁吸物品'
            else:out['heading']=flat_heading(corrected);out['compass_note']='平面校准，方向已调转180°'
        return out
    except (OSError,ValueError) as e:return {**meta,'measurement_valid':False,'compass_note':'磁场读数暂不可用','error':str(e)}

class Reader:
    def __init__(self):
        self.messages=queue.Queue(maxsize=1);self.stop=threading.Event();self.paused=threading.Event();self.refresh=threading.Event()
        self.thread=threading.Thread(target=self.run,daemon=True)
        self.thread.start()

    def publish(self,data):
        try:self.messages.get_nowait()
        except queue.Empty:pass
        self.messages.put_nowait(data)

    def run(self):
        proxy=None;claimed=False;bus_retry=0;last_diag=0;diag={};device=None;last_find=0;magnet=None;light=None;last_optical=0;optical={};last_magnet=0;mag_data={};last_proxy=0;proxy_data={};matrix=[[1,0,0],[0,1,0],[0,0,1]];matrix_source='原始轴'
        try:
            while not self.stop.is_set():
                if self.paused.is_set():self.stop.wait(.2);continue
                now=time.monotonic()
                if device is None or not device.exists() or self.refresh.is_set() or now-last_find>5:
                    device=None;magnet=None;light=None;last_find=now
                    for p in Path('/sys/bus/iio/devices').glob('iio:device*'):
                        try:
                            name=read_text(p/'name')
                            if name=='mpu6500':device=p
                            if name.lower()=='ak8963':magnet=p
                            if name=='f8-em30918':light=p
                        except OSError:pass
                    if device:matrix,matrix_source=example_matrix(device)
                if self.refresh.is_set() or now-last_diag>8:
                    self.refresh.clear();last_diag=now
                    for unit in ['f8-motion','iio-sensor-proxy','f8-bluetooth','f8-compass']:
                        try:diag[unit]=subprocess.run(['systemctl','is-active',unit],capture_output=True,text=True,timeout=2).stdout.strip() or 'unknown'
                        except (OSError,subprocess.TimeoutExpired):diag[unit]='unknown'
                data={'device':None,'scaled':{},'raw':{},'errors':[],'services':dict(diag),'orientation':'unknown','has_accelerometer':False}
                if device:
                    try:data.update(read_device(device))
                    except OSError as e:data['errors'].append(str(e));device=None
                data['example_matrix']=matrix;data['example_matrix_source']=matrix_source
                if now-last_magnet>.4:
                    last_magnet=now;mag_data=read_magnet(magnet,data.get('scaled',{}).get('accel')) if magnet else {'heading':None,'compass_note':'等待磁场设备'}
                data['magnet']=dict(mag_data);data['aux']={}
                for key,file in [('hall','hall_raw'),('motor','motor_active')]:
                    try:data['aux'][key]=int(read_text(Path('/sys/devices/platform/f8-cover-haptic')/file))
                    except (OSError,ValueError):pass
                if now-last_optical>.2:
                    last_optical=now
                    try:
                        if light is None:raise OSError('未检测到EM30918驱动')
                        optical={'available':True,'ambient_raw':int(read_text(light/'in_intensity_raw')),'proximity_raw':int(read_text(light/'proximity_raw')),'monotonic':time.monotonic()}
                    except (OSError,ValueError) as e:optical={'available':False,'error':str(e)}
                data['optical']=dict(optical)
                if proxy is None and now>=bus_retry:
                    try:
                        import dbus
                        bus=dbus.SystemBus(private=True)
                        obj=bus.get_object('net.hadess.SensorProxy','/net/hadess/SensorProxy',introspect=False)
                        proxy=(dbus.Interface(obj,'org.freedesktop.DBus.Properties'),dbus.Interface(obj,'net.hadess.SensorProxy'))
                    except Exception:proxy=None;bus_retry=now+5
                if proxy and now-last_proxy>=1:
                    try:
                        last_proxy=now
                        props=proxy[0].GetAll('net.hadess.SensorProxy',timeout=2)
                        proxy_data={'has_accelerometer':bool(props.get('HasAccelerometer',False)),'orientation':str(props.get('AccelerometerOrientation','unknown'))}
                        if proxy_data['has_accelerometer'] and not claimed:
                            proxy[1].ClaimAccelerometer(timeout=2);claimed=True
                    except Exception as e:
                        data['proxy_error']=str(e);proxy=None;claimed=False;proxy_data={};bus_retry=now+5
                data.update(proxy_data)
                self.publish(data)
                self.stop.wait(.05 if device else 1)
        finally:
            if proxy and claimed:
                try:proxy[1].ReleaseAccelerometer(timeout=2)
                except Exception:pass

class Graph(QWidget):
    def __init__(self,unit,minimum,parent=None):
        super().__init__(parent);self.unit=unit;self.minimum=minimum;self.points=collections.deque(maxlen=100)
        self.setMinimumHeight(155)

    def add(self,values):
        self.points.append(tuple(values));self.update()

    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect=self.rect();painter.fillRect(rect,QColor('#111c2d'))
        left,top,right,bottom=58,23,rect.width()-14,rect.height()-25
        limit=max(self.minimum,max((abs(v) for point in self.points for v in point),default=0)*1.15)
        painter.setFont(QFont('Sans Serif',9))
        for fraction in [-1,-.5,0,.5,1]:
            y=top+(1-fraction)*(bottom-top)/2
            painter.setPen(QPen(QColor('#26364b'),1));painter.drawLine(QPointF(left,y),QPointF(right,y))
            painter.setPen(QColor('#90a2ba'));painter.drawText(3,int(y)+4,f'{fraction*limit:.1f}')
        painter.drawText(left,15,self.unit)
        if not self.points:
            painter.setPen(QColor('#90a2ba'));painter.drawText(rect,Qt.AlignmentFlag.AlignCenter,'等待真实传感器读数')
            return
        for axis,color in enumerate(COLORS):
            path=QPainterPath()
            for i,point in enumerate(self.points):
                x=left+i*(right-left)/99;y=top+(1-point[axis]/limit)*(bottom-top)/2
                if i==0:path.moveTo(x,y)
                else:path.lineTo(x,y)
            painter.setPen(QPen(QColor(color),2));painter.drawPath(path)
        painter.setPen(QColor('#90a2ba'));painter.drawText(left,rect.height()-5,'最近 100 次采样 · X / Y / Z')

def label(text,size=12,color='#e6eefb'):
    w=QLabel(text);w.setWordWrap(True);w.setStyleSheet(f'font-size:{size}px;color:{color};');return w

class Window(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('F8 传感器观察');self.resize(1000,920);self.current=None;self.frames=0
        self.reader=Reader();self.setMinimumSize(640,450)
        host=QWidget();self.setCentralWidget(host);layout=QVBoxLayout(host);layout.setContentsMargins(22,18,22,18);layout.setSpacing(12)
        row=QHBoxLayout();title=QVBoxLayout();title.addWidget(label('F8 传感器观察',26));title.addWidget(label('陀螺仪正方体 · 水平仪 · 指南针 · 方向与开合',13,'#90a2ba'));row.addLayout(title,1)
        self.state=label('正在检查…',14,'#ffbf6b');row.addWidget(self.state);layout.addLayout(row)
        self.banner=label('正在寻找 MPU6500 与方向服务…',14);layout.addWidget(self.banner)
        self.tabs=QTabWidget();self.examples=Examples();self.fused=FusionPanel(self.examples.pose);fusion_scroll=QScrollArea();fusion_scroll.setWidgetResizable(True);fusion_scroll.setWidget(self.fused);QScroller.grabGesture(fusion_scroll.viewport(),QScroller.ScrollerGestureType.TouchGesture);self.tabs.addTab(fusion_scroll,'融合与派生传感器');scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(self.examples);QScroller.grabGesture(scroll.viewport(),QScroller.ScrollerGestureType.TouchGesture);self.tabs.addTab(scroll,'交互范例')
        raw_host=QWidget();self.tabs.addTab(raw_host,'原始数值与曲线');layout.addWidget(self.tabs,1);raw_layout=QVBoxLayout(raw_host)
        grid=QGridLayout();grid.setSpacing(14);self.axes={};self.graphs={};self.norms={}
        for col,(kind,title,unit,minimum) in enumerate([('accel','加速度','m/s²',12),('anglvel','角速度','rad/s',2)]):
            frame=QFrame();frame.setObjectName('card');box=QVBoxLayout(frame);box.setContentsMargins(15,12,15,12)
            box.addWidget(label(title,19));box.addWidget(label('传感器原始轴坐标 · SI 单位',11,'#90a2ba'))
            for axis,color in zip('XYZ',COLORS):
                value=label(f'{axis}    —',22,color);box.addWidget(value);self.axes[kind,axis]=value
            norm=label('模长 —',13,'#90a2ba');self.norms[kind]=norm;box.addWidget(norm)
            graph=Graph(unit,minimum);self.graphs[kind]=graph;box.addWidget(graph);grid.addWidget(frame,0,col)
        raw_layout.addLayout(grid,1)
        self.direction=label('方向服务：等待',18);raw_layout.addWidget(self.direction)
        self.raw=label('原始计数：—',12,'#90a2ba');raw_layout.addWidget(self.raw)
        self.details=label('设备：等待枚举',12,'#90a2ba');self.details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse);raw_layout.addWidget(self.details)
        raw_layout.addWidget(label('原始页保留芯片轴；范例页采用安装矩阵。静止时加速度模长接近9.81，角速度接近0。工具不强制旋转屏幕。',12,'#90a2ba'))
        controls=QHBoxLayout();self.pause=QPushButton('暂停');self.pause.clicked.connect(self.toggle);controls.addWidget(self.pause)
        refresh=QPushButton('重新检查');refresh.clicked.connect(self.reader.refresh.set);controls.addWidget(refresh)
        self.save=QPushButton('保存快照');self.save.clicked.connect(self.snapshot);self.save.setEnabled(False);controls.addWidget(self.save);controls.addStretch()
        close=QPushButton('关闭');close.clicked.connect(self.close);controls.addWidget(close);layout.addLayout(controls)
        self.setStyleSheet('QMainWindow,QWidget{background:#0b1422;} QFrame#card{background:#111c2d;border:1px solid #26364b;border-radius:12px;} QLabel{background:transparent;} QPushButton{color:#e6eefb;background:#21344f;border:1px solid #355071;border-radius:8px;padding:12px 20px;font-size:14px;} QPushButton:pressed{background:#365b7e;} QPushButton:disabled{color:#718298;}')
        self.tabs.setStyleSheet('QTabBar::tab{color:#c4d5eb;background:#17263b;padding:12px 20px;} QTabBar::tab:selected{background:#2c4d6a;color:white;} QTabWidget::pane{border:1px solid #26364b;}')
        self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(50)

    def tick(self):
        try:data=self.reader.messages.get_nowait()
        except queue.Empty:return
        self.current=data;self.frames+=1;self.save.setEnabled(True)
        self.examples.update_sample(data);data['examples']=dict(self.examples.state);self.fused.update_sample(data);data['fusion']=dict(self.fused.state)
        available=bool(data.get('device'));errors=data.get('errors',[])
        self.state.setText('读取异常' if errors else ('实时读取中' if available else '等待驱动'))
        self.state.setStyleSheet('font-size:14px;color:'+('#ffbf6b' if errors or not available else '#82e1bc'))
        self.banner.setText(('真实读数 · 轻缓转动观察方块，倾斜观察水平仪；静置可校零。' if available else '尚未检测到 MPU6500，等待驱动。') if not errors else '读取失败：'+errors[0])
        for kind in ['accel','anglvel']:
            values=data.get('scaled',{}).get(kind)
            for i,axis in enumerate('XYZ'):self.axes[kind,axis].setText(f'{axis}    {values[i]:+.3f}' if values else f'{axis}    —')
            self.norms[kind].setText(f'模长  {math.sqrt(sum(v*v for v in values)):.3f}' if values else '模长 —')
            if values:self.graphs[kind].add(values)
        names={'normal':'正向竖屏','bottom-up':'倒置竖屏','left-up':'左侧朝上','right-up':'右侧朝上','undefined':'未确定','unknown':'等待'}
        orientation=data.get('orientation','unknown');service='已识别' if data.get('has_accelerometer') else '未识别加速度计'
        self.direction.setText(f'方向：{names.get(orientation,orientation)}  ·  SensorProxy {service}')
        raw=data.get('raw',{});self.raw.setText(f'原始计数  加速度 {raw.get("accel","—")}    角速度 {raw.get("anglvel","—")}')
        services='  /  '.join(f'{k}: {v}' for k,v in data.get('services',{}).items())
        matrix=data.get('mount_matrix',{}).get('accel','尚未读取')
        self.details.setText(f'设备 {data.get("device") or "未枚举"}   ·   已更新 {self.frames} 次\n{services}\nIIO矩阵：{matrix}\n范例矩阵来源：{data.get("example_matrix_source")}')

    def toggle(self):
        if self.reader.paused.is_set():self.reader.paused.clear();self.pause.setText('暂停');self.state.setText('恢复读取…')
        else:self.reader.paused.set();self.pause.setText('继续');self.state.setText('已暂停');self.fused.invalidate('已暂停')

    def snapshot(self):
        directory=Path.home()/'Documents/F8-sensors';directory.mkdir(parents=True,exist_ok=True)
        filename=directory/('sensor-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.json')
        path,_=QFileDialog.getSaveFileName(self,'保存当前传感器快照',str(filename),'JSON (*.json)')
        if not path:return
        try:Path(path).write_text(json.dumps(self.current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        except OSError as e:QMessageBox.warning(self,'保存失败',str(e))

    def closeEvent(self,event):
        self.fused.invalidate('窗口已关闭');self.reader.stop.set();self.reader.thread.join(timeout=3);event.accept()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preview',type=Path);parser.add_argument('--preview-tab',type=int,choices=[0,1,2],default=0);parser.add_argument('--status-json',type=Path);args=parser.parse_args()
    app=QApplication([]);app.setApplicationName('F8 传感器观察');app.setOrganizationName('F8-PRO')
    app.setDesktopFileName('f8-sensors');window=Window();window.tabs.setCurrentIndex(args.preview_tab);window.show()
    if args.preview:
        def preview():
            window.grab().save(str(args.preview))
            if args.status_json:args.status_json.write_text(json.dumps({'samples':window.frames,'data':window.current,'reader_alive_before_close':window.reader.thread.is_alive()},ensure_ascii=False,indent=2))
            window.close();app.quit()
        QTimer.singleShot(3500,preview)
    return app.exec()

if __name__=='__main__':raise SystemExit(main())
