import paramiko
import sys

host = '8.218.89.44'
user = 'root'
password = '3cqscbrOnly1'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=10)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        print(out)
    if err:
        print('STDERR:', err)

# Find login-related files
print("=== Finding login-related Java files ===")
run("find /root/workspace/dataease/ -name '*.java' | grep -i login | head -20")

print("\n=== Finding RSA/key-related files ===")
run("find /root/workspace/dataease/ -name '*.java' | xargs grep -l 'dekey\\|RsaUtils\\|rsaKey' 2>/dev/null | head -10")

ssh.close()
