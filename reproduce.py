from pathlib import Path
import subprocess,sys,os
os.chdir(Path(__file__).parent)
subprocess.run([sys.executable,'-m','unittest','-v'],check=True)
subprocess.run([sys.executable,'run.py'],check=True)
subprocess.run([sys.executable,'-m','unittest','discover','-s','execution','-v'],check=True)
subprocess.run([sys.executable,'execution_bridge.py'],check=True)
