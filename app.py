from flask import Flask, render_template, request
import paramiko
import atexit


app = Flask(__name__)
command = 'python relay_control.py'
ssh = None
stdin = None
pi2 = None

def turn_on_api():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.1.19', username='pi', password='VerkoopBrood312')
    ssh.exec_command('python status.py')
    establish_ssh_connection()

def establish_ssh_connection():
    global ssh, stdin
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.1.19', username='pi', password='VerkoopBrood312')
    global pi2
    pi2 = paramiko.SSHClient()
    pi2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pi2.connect('192.168.1.28', username='pi', password='VerkoopBrood312')

# Function to execute the delete-locks.py script
def execute_delete_locks_script():
    ssh.exec_command('python delete-locks.py')

def start_scripts():
    pi2.exec_command('sudo reboot')
    ssh.exec_command('python read.py')
    ssh.exec_command('python keypad.py')

def turn_on_maglock(maglock):

    if maglock == '1':
        command_input = '1\n'
    elif maglock == '2':
        command_input = '2\n'
    else:
        return 'Invalid maglock selection'

    stdin.write(command_input)
    stdin.flush()

    return 'Maglock turned on'

# Function to turn off the maglock
def turn_off_maglock(maglock):
    if maglock == '0':
        command_input = '0\n'
    elif maglock == '-1':
        command_input = '-1\n'
    else:
        return 'Invalid maglock'

    stdin.write(command_input)
    stdin.flush()

    return 'Maglock turned off'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/turn_on', methods=['POST'])
def turn_on():
    maglock = request.form['maglock']
    return turn_on_maglock(maglock)

@app.route('/turn_off', methods=['POST'])
def turn_off():
    maglock = request.form['maglock']
    return turn_off_maglock(maglock)

def cleanup():
    execute_delete_locks_script()
    ssh.exec_command('pkill -f status.py')
    ssh.exec_command('pkill -f keypad.py')
    ssh.exec_command('pkill -f read.py')
    ssh.close()

if __name__ == '__main__':
    turn_on_api()
    start_scripts()
    atexit.register(cleanup)
    #execute_status_script()

    app.run(port = 8000)
