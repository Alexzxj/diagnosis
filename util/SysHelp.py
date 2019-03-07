import platform
# import psutil

def getPlatform():
    '''获取操作系统名称及版本号'''
    return platform.platform()

def getVersion():
    '''获取操作系统版本号'''
    return platform.version()

def getArchitecture():
    '''获取操作系统的位数'''
    return platform.architecture()

def getMachine():
    '''计算机类型'''
    return platform.machine()

def getNode():
    '''计算机的网络名称'''
    return platform.node()

def getProcessor():
    '''计算机处理器信息'''
    return platform.processor()

def getSystem():
    '''获取操作系统类型'''
    return platform.system()

def getUname():
    '''汇总信息'''
    return platform.uname()

def getVirtualMemoryPercent():
    '''内存的使用率'''
    # return (psutil.virtual_memory().percent)
    return 0

def getCpuPercent():
    """cpu使用率"""
    # return psutil.cpu_percent(0)
    return 0

"""获取DNS列表"""
HOST = []

