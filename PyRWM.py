import ctypes, os, numpy
import ctypes.wintypes

Windll = ctypes.windll

class RWM:
    def __init__(self):
        #Define All access permisson
        self.PROCESS_ALL_ACCESS = 0x001F0FFF
        self.MAX_PATH = 200

    def EnumProcesses(self):
        length = 100
        while 1:
            Pids = (ctypes.wintypes.DWORD*length)() 
            PidsSize = ctypes.sizeof(Pids) 
            RcvByteSize = ctypes.wintypes.DWORD() 
            if Windll.Psapi.EnumProcesses(ctypes.byref(Pids), PidsSize, ctypes.byref(RcvByteSize)):
                if RcvByteSize.value < PidsSize: 
                    return Pids, RcvByteSize.value 
                length*=2 
            else:
                return None 

    def GetPidByName(self, pName):
        Pids, RcvByteSize = self.EnumProcesses() 
        for i in range(int(RcvByteSize / ctypes.sizeof(ctypes.wintypes.DWORD))): 
            Pid = Pids[i] 
            hProcess = Windll.kernel32.OpenProcess(self.PROCESS_ALL_ACCESS, False, Pid) 
            if hProcess:
                ImageFileName = (ctypes.c_char*self.MAX_PATH)() 
                if Windll.psapi.GetProcessImageFileNameA(hProcess, ImageFileName, self.MAX_PATH) > 0: 
                    fName = os.path.basename(ImageFileName.value).decode() 
                    if fName == pName: 
                        self.CloseHandle(hProcess) 
                        return Pid
            self.CloseHandle(hProcess)
        return 0 

    def OpenProcess(self, dwProcessId):
        bInheritHandle = False
        hProcess = Windll.kernel32.OpenProcess(self.PROCESS_ALL_ACCESS, bInheritHandle, dwProcessId)
        if hProcess:
            return hProcess

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
            ReadBuffer = (ctypes.wintypes.BYTE*length)()
            lpBuffer = ctypes.byref(ReadBuffer)
            nSize = ctypes.sizeof(ReadBuffer) 
            Windll.kernel32.ReadProcessMemory(hProcess, addr, lpBuffer, nSize, None) # Error 299 is fine.
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
            ReadBuffer = ctypes.c_uint() 
            lpBuffer = ctypes.byref(ReadBuffer) 
            nSize = ctypes.sizeof(ReadBuffer) 
            lpNumberOfBytesRead = ctypes.c_ulong(0) 
            if not Windll.kernel32.ReadProcessMemory(hProcess, lpBaseAddress, lpBuffer, nSize, lpNumberOfBytesRead):
                print("Failed to Read!")
            return ReadBuffer
        except (BufferError, ValueError, TypeError) as e: 
            self.CloseHandle(hProcess)
            return f"{str(e)} raised on {hProcess} handle. Err Code : {self.GetLastError()}"

    def WriteProcessMemory(self, hProcess, lpBaseAddress, value):
        try:
            WriteBuffer = ctypes.c_uint(value) 
            lp = ctypes.byref(WriteBuffer)
            lpBuffer = ctypes.byref(WriteBuffer) 
            nSize = ctypes.sizeof(WriteBuffer) 
            lpNumberOfBytesWritten = ctypes.c_ulong(0) 
            if not Windll.kernel32.WriteProcessMemory(hProcess, lpBaseAddress, lpBuffer, nSize, lpNumberOfBytesWritten):
                print("Failed to Write!")
        except (BufferError, ValueError, TypeError) as e: 
            self.CloseHandle(hProcess)
            return f"{str(e)} raised on {hProcess} handle. Err Code : {self.GetLastError()}"

    def CloseHandle(self, hProcess):
        Windll.kernel32.CloseHandle(hProcess)
        return self.GetLastError()
    
    def GetLastError(self):
        err = Windll.kernel32.GetLastError()
        self.ClearLastError()
        return err
    
    def ClearLastError(self): 
        Windll.kernel32.SetLastError(0)