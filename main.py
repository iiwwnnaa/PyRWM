import PyRWM, ctypes

if __name__ == '__main__':
    rwm = PyRWM.RWM()
    pid = rwm.GetPidByName("notepad.exe")
    print(pid)
    hModule = rwm.GetModule(pid, "notepad.exe")
    baseAddr = ctypes.addressof(hModule.modBaseAddr.contents)
    endAddr = baseAddr + hModule.modBaseSize
    hProcess = rwm.OpenProcess(pid)
    signature = "72 69 ?? 69 ?? ?? 67 65"
    addr = rwm.GetAddressFromSignature(hProcess, signature, startAddr=baseAddr, endAddr=endAddr)
    #print(hex(rwm.GetPointer(hProcess, baseAddr, offsets=[0x3DC, 0x540, 0x1C, 0xA0, 0xC, 0x218, 0x4B0])))
    #print(hex(rwm.ReadProcessMemory(hProcess, baseAddr).value))
    #rwm.WriteProcessMemory(hProcess,baseaddr, 0x64)
    #print(rwm.ReadProcessMemory(hProcess, baseaddr).value)