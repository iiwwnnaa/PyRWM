import ctypes, os
import ctypes.wintypes

Windll = ctypes.windll

class Re4dWriteMemory:
    def __init__(self):
        #Define All access permisson
        self.PROCESS_ALL_ACCESS = 0x001F0FFF
        self.MAX_PATH = 200
        
    def EnumProcesses(self):
        length = 100 # length for assign pid list
        while 1:
            Pids = (ctypes.wintypes.DWORD*length)() # assign empty pid list (DWORD 4byte * length)
            PidsSize = ctypes.sizeof(Pids) # calculate byte size of pid list
            RByteSize = ctypes.wintypes.DWORD() # assign DWORD type space for returned byte size from Pids
            if Windll.Psapi.EnumProcesses(ctypes.byref(Pids), PidsSize, ctypes.byref(RByteSize)):
                if RByteSize.value < PidsSize: # if current pid list size is fine
                    return Pids, RByteSize.value # return Pids and PidsSize
                else:  # if pid list is small
                    length*=2 # extend Pid list
            else:
                return None #Error

    def GetPidByName(self, pName):
        Pids, RByteSize = self.EnumProcesses() # Get List of Processes on System
        for i in range(int(RByteSize / ctypes.sizeof(ctypes.wintypes.DWORD))): # Divide by DWORD size for Read Pid list
            Pid = Pids[i] # Read Pid list in order
            hProcess = Windll.kernel32.OpenProcess(self.PROCESS_ALL_ACCESS, False, Pid) # Get Process Handle
            if hProcess:
                ImageFileName = (ctypes.c_char*self.MAX_PATH)() # assign char type space for returned file name
                if Windll.psapi.GetProcessImageFileNameA(hProcess, ImageFileName, self.MAX_PATH) > 0: #If function succeeds
                    fName = os.path.basename(ImageFileName.value).decode() #Extract basename from full path 
                    if fName == pName: #If this process is matched to pName
                        self.CloseHandle(hProcess) #Close handle and return pid
                        return Pid
            self.CloseHandle(hProcess)
        return 0 # FAILED to find process

    def OpenProcess(self, dwProcessId):
        bInheritHandle = False
        hProcess = Windll.kernel32.OpenProcess(self.PROCESS_ALL_ACCESS, bInheritHandle, dwProcessId)
        if hProcess:
            return hProcess

    def GetPointer(self, hProcess, lpBaseAddress, offsets):
        pass

    def ReadProcessMemory(self, hProcess, lpBaseAddress):
        try:
            ReadBuffer = ctypes.c_uint() # assign unsigned int buffer for reading content from lpBaseAddress
            lpBuffer = ctypes.byref(ReadBuffer) # assign pointer and point ReadBuffer
            nSize = ctypes.sizeof(ReadBuffer) # the number of bytes to be read from the process
            lpNumberOfBytesRead = ctypes.c_ulong(0) # A pointer to a variable that receives the number of bytes transferred into the lpBuffer.
            if not Windll.kernel32.ReadProcessMemory(hProcess, lpBaseAddress, lpBuffer, nSize, lpNumberOfBytesRead):
                print("Failed to Read!")
            return ReadBuffer
        except (BufferError, ValueError, TypeError) as e: #Handlig Errors
            self.CloseHandle(hProcess)
            return f"{str(e)} raised on {hProcess} handle. Err Code : {self.GetLastError()}"

    def WriteProcessMemory(self, hProcess, lpBaseAddress, value):
        try:
            WriteBuffer = ctypes.c_uint() # assign unsigned int buffer for write content to lpBaseAddress
            lpBuffer = ctypes.byref(WriteBuffer) # assign pointer and point WriteBuffer
            nSize = ctypes.sizeof(WriteBuffer) # the number of bytes to be write to the process
            lpNumberOfBytesWritten = ctypes.c_ulong(0) # A pointer to a variable that receives the number of bytes transferred into the lpBuffer.
            if not Windll.kernel32.WriteProcessMemory(hProcess, lpBaseAddress, lpBuffer, nSize, lpNumberOfBytesWritten):
                print("Failed to Write!")

        except (BufferError, ValueError, TypeError) as e: #Handlig Errors
            self.CloseHandle(hProcess)
            return f"{str(e)} raised on {hProcess} handle. Err Code : {self.GetLastError()}"
    
    def CloseHandle(self, hProcess):
        Windll.kernel32.CloseHandle(hProcess)
        return self.GetLastError()
    
    def GetLastError(self):
        err = Windll.kernel32.GetLastError()
        self.ClearLastError() # Clear after get last Error
        return err
    
    def ClearLastError(self): 
        Windll.kernel32.SetLastError(0)
    
if __name__ == '__main__':
    rwm = Re4dWriteMemory()
    pid = rwm.GetPidByName("Tutorial-i386.exe")
    hProcess = rwm.OpenProcess(pid)
    rwm.ReadProcessMemory(hProcess, 0x0)
    rwm.WriteProcessMemory(hProcess, 0x0, 1)
    rwm.ReadProcessMemory(hProcess, 0x0).value