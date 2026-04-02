"""Connect to StarRocks via dev server SSH and adjust query CPU limit."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import paramiko
import time

dev_host = '8.218.89.44'
dev_user = 'root'
dev_pwd = '3cqscbrOnly1'

sr_host = 'fe-c-907795efe3201917-internal.starrocks.aliyuncs.com'
sr_port = 9030
sr_db = 'ads'
sr_user = 'dataease'
sr_pwd = 'Haoran$2026'

print("Connecting to dev server via SSH...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(dev_host, username=dev_user, password=dev_pwd, timeout=30)
print("SSH connected!")

mysql_cmd = f'mysql -h {sr_host} -P {sr_port} -u {sr_user} -p"{sr_pwd}" {sr_db}'

# Test connection and check current limits
commands = [
    f'{mysql_cmd} -e "SELECT VERSION();"',
    f'{mysql_cmd} -e "SHOW VARIABLES LIKE \'%big_query%\';"',
    f'{mysql_cmd} -e "SHOW VARIABLES LIKE \'%query_cpu%\';"',
    f'{mysql_cmd} -e "SHOW VARIABLES LIKE \'%resource%limit%\';"',
]

for cmd in commands:
    print(f"\n>>> {cmd.split('-e')[1] if '-e' in cmd else cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        print(f"OUT: {out[:500]}")
    if err and 'Warning' not in err:
        print(f"ERR: {err[:500]}")

ssh.close()
print("\nDone!")
