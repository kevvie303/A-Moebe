from flask import Flask, render_template, request
import paramiko

app = Flask(__name__)
command = 'python relay_control.py'
ssh = None
stdin = None

# Function to establish the SSH connection
def establish_ssh_connection():
    global ssh, stdin
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.1.19', username='pi', password='VerkoopBrood312')
    ssh.exec_command('python read.py')
    ssh.exec_command('python keypad.py')
    stdin = ssh.exec_command(command)[0]

#def execute_status_script():
    #ssh.exec_command('python status.py')
# Function to turn on the maglock
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

if __name__ == '__main__':
    establish_ssh_connection()
    #execute_status_script()

    app.run(port = 8000)
