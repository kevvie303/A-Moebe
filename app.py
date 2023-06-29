from flask import Flask, render_template, request, redirect, jsonify
import paramiko
import atexit
import os
import requests

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
    stdin = ssh.exec_command(command)[0]
    global pi2
    pi2 = paramiko.SSHClient()
    pi2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pi2.connect('192.168.1.28', username='pi', password='VerkoopBrood312')

# Function to execute the delete-locks.py script
def execute_delete_locks_script():
    ssh.exec_command('python delete-locks.py')

def start_scripts():
    pi2.exec_command('python status.py')
    ssh.exec_command('python read.py')
    ssh.exec_command('python keypad.py')

@app.route('/add_music', methods=['POST'])
def add_music():
    file = request.files['file']
    if file:
        try:
            # Create an SFTP client to transfer the file
            sftp = pi2.open_sftp()
            
            # Get the file name and extension
            filename, file_extension = os.path.splitext(file.filename)
            
            # Modify the file path to be relative to the Flask application
            local_path = os.path.join(app.root_path, 'uploads', file.filename)
            
            # Save the file to the modified local path
            file.save(local_path)
            
            # Save the file to the Music folder on the Pi
            remote_path = '/home/pi/Music/' + filename + file_extension
            sftp.put(local_path, remote_path)
            
            # Close the SFTP client
            sftp.close()
            
            # Delete the local file after transferring
            os.remove(local_path)
            
            return 'Music added successfully!'
        except IOError as e:
            return f'Error: {str(e)}'
        finally:
            # Close the SSH connection
            print("h")
    else:
        return 'No file selected.'

@app.route('/media_control')
def media_control():
    try:
        # Create an SFTP client to list files in the Music folder
        sftp = pi2.open_sftp()
        
        # List all MP3 files in the Music folder
        remote_path = '/home/pi/Music'
        mp3_files = [file for file in sftp.listdir(remote_path) if file.endswith('.mp3')]
        
        return render_template('media_control.html', mp3_files=mp3_files)
    except IOError as e:
        return f'Error: {str(e)}'
    finally:
        # Close the SFTP client and SSH connection
        sftp.close()

@app.route('/delete_music', methods=['POST'])
def delete_music():
    file = request.form.get('file')
    if file:

        try:
            # Create an SFTP client to delete the selected file
            sftp = pi2.open_sftp()
            
            # Delete the selected file from the Music folder
            remote_path = '/home/pi/Music/' + file
            sftp.remove(remote_path)
            
            return redirect('/media_control')
        except IOError as e:
            return f'Error: {str(e)}'
        finally:
            # Close the SFTP client and SSH connection
            sftp.close()
    else:
        return 'No file selected.'


@app.route('/file_selection')
def file_selection():
    stdin, stdout, stderr = pi2.exec_command('ls ~/Music')
    music_files = stdout.read().decode().splitlines()
    return render_template('file_selection.html', music_files=music_files)

@app.route('/play_music', methods=['POST'])
def play_music():
    selected_file = request.form['file']
    pi2.exec_command(f'mpg123 Music/{selected_file} &')
    return 'Music started on pi2'

@app.route('/stop_music', methods=['POST'])
def stop_music():
    stdin, stdout, stderr = pi2.exec_command('pkill -9 mpg123')
    return 'Music stopped on pi2'

@app.route('/pause_music', methods=['POST'])
def pause_music():
    # Execute the command to pause the music using mpg123
    command = 'mpg123 -s'
    stdin, stdout, stderr = pi2.exec_command(command)
    
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    print('Command output:', output)
    print('Command error:', error)
    
    return 'Music paused on the Pi'


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


API_URL = 'http://192.168.1.28:5001/current_state'

@app.route('/get_state', methods=['GET'])
def get_state():
    try:
        # Make a GET request to the API to fetch the current state
        response = requests.get(API_URL)
        if response.status_code == 200:
            state = response.json().get('state')
        else:
            state = 'unknown'
    except requests.exceptions.RequestException:
        state = 'unknown'
    
    return jsonify({'state': state})

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
    pi2.exec_command('pkill -f status.py')
    ssh.exec_command('pkill -f keypad.py')
    ssh.exec_command('pkill -f read.py')
    ssh.close()

if __name__ == '__main__':
    turn_on_api()
    start_scripts()
    atexit.register(cleanup)
    #execute_status_script()

    app.run(port = 8000)
