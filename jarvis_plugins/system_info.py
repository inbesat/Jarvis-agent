"""
Sample Jarvis Plugin - System Info
Shows system information when run.
"""
PLUGIN_NAME = "system_info"

def run(args=""):
    import platform
    import psutil
    try:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return (
            f"System Info:\n"
            f"  OS: {platform.system()} {platform.release()}\n"
            f"  CPU: {cpu}% used\n"
            f"  RAM: {mem.percent}% used ({mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB)\n"
            f"  Disk: {disk.percent}% used ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)\n"
            f"  Python: {platform.python_version()}"
        )
    except ImportError:
        return (
            f"System Info:\n"
            f"  OS: {platform.system()} {platform.release()}\n"
            f"  Python: {platform.python_version()}\n"
            f"  (Install psutil for detailed stats: pip install psutil)"
        )
