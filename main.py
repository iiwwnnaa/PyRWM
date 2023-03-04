import PyRWM

if __name__ == '__main__':
    rwm = PyRWM.RWM()
    pid = rwm.GetPidByName("Tutorial-i386.exe")
    hProcess = rwm.OpenProcess(pid)
    baseaddr = 0x00400000
    #print(hex(baseaddr))
    signature = [0x6f, -1, 0x72, 0x61, -1, 0x20, -1, 0x61]
    print(rwm.GetAddressFromSignature(hProcess, baseaddr, signature))
    #print(hex(rwm.GetPointer(hProcess, baseaddr, offsets=[0x3DC, 0x540, 0x1C, 0xA0, 0xC, 0x218, 0x4B0])))
    #print(rwm.ReadProcessMemory(hProcess, baseaddr).value)
    #rwm.WriteProcessMemory(hProcess,baseaddr, 0x64)
    #print(rwm.ReadProcessMemory(hProcess, baseaddr).value)