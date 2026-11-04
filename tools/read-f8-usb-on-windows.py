"""Read hub metadata/descriptors for the user's 152d:0583 device. No disk I/O."""
import ctypes as C,json,struct,sys
from ctypes import wintypes as W
from pathlib import Path
assert sys.platform=='win32'
class GUID(C.Structure):
    _fields_=[('a',W.DWORD),('b',W.WORD),('c',W.WORD),('d',C.c_ubyte*8)]
class Interface(C.Structure):
    _fields_=[('size',W.DWORD),('guid',GUID),('flags',W.DWORD),('reserved',C.c_void_p)]
guid=GUID(0xf18a0e88,0xc30c,0x11d0,(C.c_ubyte*8)(0x88,0x15,0x00,0xa0,0xc9,0x06,0xbe,0xd8))
setup=C.WinDLL('setupapi',use_last_error=True);kernel=C.WinDLL('kernel32',use_last_error=True)
setup.SetupDiGetClassDevsW.argtypes=[C.POINTER(GUID),W.LPCWSTR,W.HWND,W.DWORD];setup.SetupDiGetClassDevsW.restype=C.c_void_p
setup.SetupDiEnumDeviceInterfaces.argtypes=[C.c_void_p,C.c_void_p,C.POINTER(GUID),W.DWORD,C.POINTER(Interface)];setup.SetupDiEnumDeviceInterfaces.restype=W.BOOL
setup.SetupDiGetDeviceInterfaceDetailW.argtypes=[C.c_void_p,C.POINTER(Interface),C.c_void_p,W.DWORD,C.POINTER(W.DWORD),C.c_void_p];setup.SetupDiGetDeviceInterfaceDetailW.restype=W.BOOL
setup.SetupDiDestroyDeviceInfoList.argtypes=[C.c_void_p];setup.SetupDiDestroyDeviceInfoList.restype=W.BOOL
kernel.CreateFileW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,C.c_void_p,W.DWORD,W.DWORD,C.c_void_p];kernel.CreateFileW.restype=C.c_void_p
kernel.DeviceIoControl.argtypes=[C.c_void_p,W.DWORD,C.c_void_p,W.DWORD,C.c_void_p,W.DWORD,C.POINTER(W.DWORD),C.c_void_p];kernel.DeviceIoControl.restype=W.BOOL
kernel.CloseHandle.argtypes=[C.c_void_p];kernel.CloseHandle.restype=W.BOOL
invalid=C.c_void_p(-1).value
def ioctl(handle,code,payload,size=4096):
    buf=C.create_string_buffer(size);C.memmove(buf,payload,len(payload));got=W.DWORD()
    ok=kernel.DeviceIoControl(handle,code,buf,size,buf,size,C.byref(got),None)
    if not ok:raise C.WinError(C.get_last_error())
    return bytes(buf.raw[:got.value])
info=setup.SetupDiGetClassDevsW(C.byref(guid),None,None,0x12)
assert info!=invalid
devices=[];errors=[];hubs=0
try:
    for index in range(64):
        interface=Interface();interface.size=C.sizeof(interface)
        if not setup.SetupDiEnumDeviceInterfaces(info,None,C.byref(guid),index,C.byref(interface)):
            assert C.get_last_error()==259,C.WinError(C.get_last_error());break
        needed=W.DWORD();setup.SetupDiGetDeviceInterfaceDetailW(info,C.byref(interface),None,0,C.byref(needed),None)
        buf=C.create_string_buffer(needed.value);struct.pack_into('<I',buf,0,8 if C.sizeof(C.c_void_p)==8 else 6)
        if not setup.SetupDiGetDeviceInterfaceDetailW(info,C.byref(interface),buf,needed.value,None,None):
            errors.append({'hub_index':index,'detail_error':C.get_last_error()});continue
        path=C.wstring_at(C.addressof(buf)+4)
        handle=kernel.CreateFileW(path,0,3,None,3,0,None)
        if handle==invalid:
            errors.append({'hub_index':index,'open_error':C.get_last_error()});continue
        hubs+=1
        try:
            node=ioctl(handle,0x220408,struct.pack('<I',0),1024)
            ports=node[6];assert 0<ports<=127
            for port in range(1,ports+1):
                try:raw=ioctl(handle,0x220448,struct.pack('<I',port))
                except OSError:continue
                if len(raw)<25 or raw[4:6]!=b'\x12\x01':continue
                vid,pid=struct.unpack_from('<HH',raw,12)
                if (vid,pid)!=(0x152d,0x0583):continue
                bcd=struct.unpack_from('<H',raw,6)[0]
                device={'vid':'152d','pid':'0583','hub_index':index,'port_index':port,'bcd_usb':hex(bcd),'speed_code':raw[23],
                        'device_class':raw[8],'configuration_count':raw[21],'descriptor_read_only':True}
                # USB_DESCRIPTOR_REQUEST: connection index + 8-byte setup packet.
                request=struct.pack('<IBBHHH',port,0x80,6,0x0200,0,4084)
                try:
                    config=ioctl(handle,0x220410,request)
                    body=config[12:];assert body[:2]==b'\x09\x02'
                    total=struct.unpack_from('<H',body,2)[0];assert 9<=total<=len(body)
                    device.update(configuration_total_bytes=total,configuration_attributes=hex(body[7]),max_power_raw=body[8],
                                  declared_max_power_ma=body[8]*(8 if bcd>=0x0300 else 2))
                    interfaces=[];pos=0
                    while pos<total:
                        length,kind=body[pos:pos+2];assert length>=2 and pos+length<=total
                        if kind==4 and length>=9:interfaces.append({'class':body[pos+5],'subclass':body[pos+6],'protocol':body[pos+7]})
                        pos+=length
                    device['interfaces']=interfaces
                except (OSError,AssertionError) as e:device['configuration_error']=str(e)
                devices.append(device)
        except (OSError,AssertionError) as e:errors.append({'hub_index':index,'query_error':str(e)})
        finally:kernel.CloseHandle(handle)
finally:setup.SetupDiDestroyDeviceInfoList(info)
report={'scope':'Read-only USB hub descriptor query, no volumes/files/disk sectors accessed','hub_handles_opened':hubs,'matching_devices':devices,'errors':errors,
        'api_reference':'https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/usbioctl/ni-usbioctl-ioctl_usb_get_descriptor_from_node_connection'}
out=Path(__file__).resolve().parents[1]/'local/hardware/armbian-native-usb-20261101/pc-usb-descriptor01.json'
assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
