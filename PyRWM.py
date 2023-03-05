import os, numpy
from ctypes import *
from ctypes.wintypes import *

win_Module32First = windll.kernel32.Module32First
win_Module32Next = windll.kernel32.Module32Next
win_OpenProcess = windll.kernel32.OpenProcess
win_GetProcessImageFileNameA = windll.psapi.GetProcessImageFileNameA
win_CreateToolhelp32Snapshot = windll.kernel32.CreateToolhelp32Snapshot
win_EnumProcesses = windll.Psapi.EnumProcesses
win_ReadProcessMemory = windll.kernel32.ReadProcessMemory
win_WriteProcessMemory = windll.kernel32.WriteProcessMemory
win_GetLastError = windll.kernel32.GetLastError
win_SetLastError = windll.kernel32.SetLastError
win_CloseHandle = windll.kernel32.CloseHandle 

class MODULEENTRY32(Structure):
    _fields_ = [
    ( 'dwSize' , DWORD),
    ( 'th32ModuleID' , DWORD),
    ( 'th32ProcessID' , DWORD),
    ( 'GlblcntUsage' , DWORD),
    ( 'ProccntUsage' , DWORD),
    ( 'modBaseAddr' , POINTER(BYTE)),
    ( 'modBaseSize' , DWORD),
    ( 'hModule' , HMODULE),
    ( 'szModule' , c_char * 256),
    ( 'szExePath' , c_char * 260) ]

class RWM:
    def __init__(self):
        #Define All access permisson
        self.PROCESS_ALL_ACCESS = 0x001F0FFF
        self.TH32CS_SNAPMODULE = 0x00000008
        self.MAX_PATH = 200
    
    def EnumProcesses(self):
        length = 100
        while 1:
            Pids = (DWORD*length)() 
            PidsSize = sizeof(Pids) 
            RcvByteSize = DWORD() 
            if win_EnumProcesses(byref(Pids), PidsSize, byref(RcvByteSize)):
                if RcvByteSize.value < PidsSize: 
                    return Pids, RcvByteSize.value 
                length*=2 
            else:
                return None 

    def GetPidByName(self, pName):
        Pids, RcvByteSize = self.EnumProcesses() 
        for i in range(int(RcvByteSize / sizeof(DWORD))): 
            Pid = Pids[i] 
            hProcess = win_OpenProcess(self.PROCESS_ALL_ACCESS, False, Pid) 
            if hProcess:
                ImageFileName = (c_char*self.MAX_PATH)() 
                if win_GetProcessImageFileNameA(hProcess, ImageFileName, self.MAX_PATH) > 0: 
                    fName = os.path.basename(ImageFileName.value).decode() 
                    if fName == pName:
                        self.CloseHandle(hProcess) 
                        return Pid
            self.CloseHandle(hProcess)
        return 0 #Failed to get PID

    def OpenProcess(self, dwProcessId):
        bInheritHandle = False
        hProcess = win_OpenProcess(self.PROCESS_ALL_ACCESS, bInheritHandle, dwProcessId)
        if hProcess:
            return hProcess

    def GetModule(self, Pid, pName):
        me32 = MODULEENTRY32()
        me32.dwSize = sizeof( MODULEENTRY32 )
        hModuleSnap = c_void_p(0)
        hModuleSnap = win_CreateToolhelp32Snapshot(self.TH32CS_SNAPMODULE, Pid)
        if win_Module32First(hModuleSnap, byref(me32)):
            if me32.szModule.decode() == pName:
                self.CloseHandle(hModuleSnap)
                return me32
            else:
                win_Module32Next(hModuleSnap, byref(me32))
                while int(GetLastError()) != 18: #ERROR_NO_MORE_FILES
                    if me32.szModule.decode() == pName:
                        self.CloseHandle(hModuleSnap)
                        return me32
                    win_Module32Next(hModuleSnap, byref(me32))
        self.CloseHandle(hModuleSnap)

    def GetPointer(self, hProcess, lpBaseAddress, offsets):
        length = len(offsets)
        if offsets is not None:
            ptrVal = self.ReadProcessMemory(hProcess, lpBaseAddress).value 
            if length == 1: 
                return ptrVal 
            baseaddr = ptrVal 
            for i, val in enumerate(offsets):
                baseaddr += val 
                ptrVal2 = self.ReadProcessMemory(hProcess, baseaddr).value 
                if i == length-1: 
                    return baseaddr 
                baseaddr = ptrVal2 
        return lpBaseAddress

    def GetAddressFromSignature(self, hProcess, signature, startAddr=0x00400000, endAddr=0xFFFFFFFF): #for Win32 Process
        tmp = []
        for i in signature.split(" "):
            if i == "??":
                tmp.append(-1)
            else:
                tmp.append(int(i, 16))
        signature = numpy.array(tmp)
        length = endAddr - startAddr
        if length > 0x20000000: #if length is bigger than 512MB
            length = 0x20000000
        for addr in range(startAddr, endAddr+1, length):
            ReadBuffer = (BYTE*length)()
            lpBuffer = byref(ReadBuffer)
            nSize = sizeof(ReadBuffer)
            win_ReadProcessMemory(hProcess, c_void_p(addr) , lpBuffer, nSize, None) # Error 299 is fine.
            ReadBuffer = numpy.array(ReadBuffer)
            for offset, val in enumerate(ReadBuffer):
                addr2 = addr+offset
                for i, v in enumerate(ReadBuffer[offset:]):
                    if signature[i] != -1 and signature[i] != (v & 0xff):
                        break
                    if i == len(signature)-1:
                        return addr2

    def ReadProcessMemory(self, hProcess, lpBaseAddress):
        try:
            ReadBuffer = c_uint() 
            lpBuffer = byref(ReadBuffer) 
            nSize = sizeof(ReadBuffer) 
            if not win_ReadProcessMemory(hProcess, c_void_p(lpBaseAddress), lpBuffer, nSize, None):
                print("Failed to Read!")
            return ReadBuffer
        except (BufferError, ValueError, TypeError) as e: 
            self.CloseHandle(hProcess)
            return f"{str(e)} raised on {hProcess} handle. Err Code : {self.GetLastError()}"

    def WriteProcessMemory(self, hProcess, lpBaseAddress, value):
        try:
            WriteBuffer = c_uint(value) 
            lp = byref(WriteBuffer)
            lpBuffer = byref(WriteBuffer) 
            nSize = sizeof(WriteBuffer) 
            if not win_WriteProcessMemory(hProcess, c_void_p(lpBaseAddress), lpBuffer, nSize, None):
                print("Failed to Write!")
        except (BufferError, ValueError, TypeError) as e: 
            self.CloseHandle(hProcess)
            return f"{str(e)} raised on {hProcess} handle. Err Code : {self.GetLastError()}"

    def CloseHandle(self, hProcess):
        win_CloseHandle(hProcess)
        return self.GetLastError()
    
    def GetLastError(self):
        err = win_GetLastError()
        self.ClearLastError()
        return err
    
    def ClearLastError(self): 
        win_SetLastError(0)