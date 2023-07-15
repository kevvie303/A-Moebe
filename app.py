from flask import Flask, render_template, request, redirect, jsonify
import paramiko
import atexit
import os
import time
import requests
import subprocess
import signal
import sys
import threading
from pydub import AudioSegment
from pydub.playback import _play_with_pyaudio

app = Flask(__name__)
command = 'python relay_control.py'
ssh = None
stdin = None
pi2 = None
romy = False
fade_duration = 3  # Fade-out duration in seconds
fade_interval = 0.1  # Interval between volume adjustments in seconds
fade_steps = int(fade_duration / fade_interval)  # Number of fade steps
sensor_1_triggered = False
sensor_2_triggered = False

def turn_on_api():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.1.19', username='pi', password='VerkoopBrood312')
    ssh.exec_command('python status.py')
    establish_ssh_connection()

def establish_ssh_connection():
    global ssh, stdin
    
    if ssh is None or not ssh.get_transport().is_active():
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('192.168.1.19', username='pi', password='VerkoopBrood312')
        stdin = ssh.exec_command(command)[0]
    
    global pi2
    
    if pi2 is None or not pi2.get_transport().is_active():
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
            # Get the file extension
            filename, file_extension = os.path.splitext(file.filename)
            
            # Check if the file extension is allowed
            allowed_extensions = ['.mp3', '.wav', '.ogg']
            if file_extension.lower() in allowed_extensions:
                # Create an SFTP client to transfer the file
                sftp = pi2.open_sftp()
                
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
            else:
                return 'Invalid file type. Only .mp3, .wav, and .ogg files are allowed.'
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

# Global variable to keep track of the currently playing music file
current_file = None

@app.route('/pause_music', methods=['POST'])
def pause_music():
    global current_file

    if current_file:
        # Fade out the music gradually
        fade_duration = 2  # Adjust the fade duration as needed
        fade_interval = 0.1  # Adjust the fade interval as needed
        max_volume = 100

        # Calculate the step size for volume reduction
        step_size = max_volume / (fade_duration / fade_interval)

        # Get the process ID of the mpg123 process
        command = f'pgrep -f "mpg123 Music/{current_file}"'
        stdin, stdout, stderr = pi2.exec_command(command)
        process_id = stdout.read().decode().strip()

        if process_id:
            # Reduce the volume gradually
            for volume in reversed(range(0, max_volume, int(step_size))):
                command = f'amixer set Master {volume}%'
                pi2.exec_command(command)
                time.sleep(fade_interval)

                # Check if the volume reached 0
                if volume <= 0:
                    # Pause the music by sending a SIGSTOP signal to the mpg123 process
                    command = f'pkill -STOP -f "mpg123 Music/{current_file}"'
                    pi2.exec_command(command)

            return 'Music paused on pi2'
        else:
            return 'No music is currently playing'
    else:
        return 'No music is currently playing'

@app.route('/resume_music', methods=['POST'])
def resume_music():
    global current_file

    if current_file:
        # Fade in the music gradually
        fade_duration = 2  # Adjust the fade duration as needed
        fade_interval = 0.1  # Adjust the fade interval as needed
        target_volume = 100  # Adjust the desired volume level

        # Calculate the step size for volume increase
        step_size = target_volume / (fade_duration / fade_interval)

        # Get the process ID of the mpg123 process
        command = f'pgrep -f "mpg123 Music/{current_file}"'
        stdin, stdout, stderr = pi2.exec_command(command)
        process_id = stdout.read().decode().strip()

        if process_id:
            # Increase the volume gradually
            for volume in range(0, target_volume + 1, int(step_size)):
                command = f'amixer set Master {volume}%'
                pi2.exec_command(command)
                time.sleep(fade_interval)

                command = f'pkill -CONT -f "mpg123 Music/{current_file}"'
                pi2.exec_command(command)

            return 'Music resumed on pi2'
        else:
            return 'No music is currently playing'
    else:
        return 'No music is currently playing'

@app.route('/play_music', methods=['POST'])
def play_music():
    global current_file
    selected_file = request.form['file']
    current_file = selected_file
    command = f'mpg123 Music/{selected_file} &'
    pi2.exec_command(command)
    return 'Music started on pi2'

@app.route('/stop_music', methods=['POST'])
def stop_music():
    stdin, stdout, stderr = pi2.exec_command('pkill -9 mpg123')
    return 'Music stopped on pi2'


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

@app.route('/send_script')
def send_script():
    script_path = 'test.py'
    target_ip = '192.168.1.28'
    target_username = 'pi'
    target_directory = '~/'

    # Construct the scp command
    scp_command = f'scp {script_path} {target_username}@{target_ip}:{target_directory}'

    try:
        # Execute the scp command
        subprocess.run(scp_command, shell=True, check=True)
        return 'Script sent successfully!'
    except subprocess.CalledProcessError as e:
        return f'Error occurred while sending script: {e}'
    
def reset_sensors():
    global sensor_1_triggered, sensor_2_triggered
    if sensor_2_triggered or sensor_1_triggered:
        time.sleep(1)
        sensor_1_triggered = False
        sensor_2_triggered = False
        print("Trigger flags reset.")

def continuous_reset_sensors():
    while True:
        reset_sensors()
def execute_code():
    stdin.write('0\n')
    stdin.flush()
    print("Code executed on the server Pi.")

@app.route('/reboot-maglock-pi', methods=['POST'])
def reboot_mag_pi():
    # ssh.exec_command('sudo reboot')
    # time.sleep(60)
    # establish_ssh_connection()
    # time.sleep(3)
    # ssh.exec_command('python delete-locks.py')
    # ssh.exec_command('python read.py')
    # ssh.exec_command('python keypad.py')
    return "Magpi reset succesfully!"

@app.route('/trigger', methods=['POST'])
def handle_trigger():
    global sensor_1_triggered, sensor_2_triggered

    sensor_data = request.get_json()
    # print("Sensor triggered:", sensor_data["sensor"])

    if sensor_data["sensor"] == "Sensor 1":
        sensor_1_triggered = True
    elif sensor_data["sensor"] == "Sensor 2":
        sensor_2_triggered = True
    elif sensor_data["sensor"] == "turn off":
        sensor_1_triggered = False
        sensor_2_triggered = False
    if sensor_1_triggered and sensor_2_triggered:
        execute_code()
    return "Trigger handled."
def handle_interrupt(signal, frame):
    print("Interrupt received. Shutting down...")
    # Add any additional cleanup or termination logic here
    sys.exit()
TIMER_FILE = 'timer_value.txt'  # File to store the timer value
timer_value = 3600  # Initial timer value in seconds
timer_thread = None  # Reference to the timer thread
speed = 1
timer_running = False  # Flag to indicate if the timer is running
def read_timer_value():
    try:
        with open(TIMER_FILE, 'r') as file:
            return float(file.read().strip())
    except FileNotFoundError:
        return timer_value  # Default timer value if the file doesn't exist

def write_timer_value(value):
    with open(TIMER_FILE, 'w') as file:
        file.write(str(value))

def update_timer():
    global timer_value, speed, timer_running
    while timer_value > 0 and timer_running:
        timer_value = max(timer_value - speed, 0)
        write_timer_value(timer_value)
        threading.Event().wait(1)

@app.route('/timer/start', methods=['POST'])
def start_timer():
    global timer_thread, timer_value, speed, timer_running

    if timer_thread is None or not timer_thread.is_alive():
        timer_value = 3600  # Reset timer value to 60 minutes
        write_timer_value(timer_value)
        timer_running = True
        timer_thread = threading.Thread(target=update_timer)
        timer_thread.daemon = True
        timer_thread.start()

    return 'Timer started'

@app.route('/timer/stop', methods=['POST'])
def stop_timer():
    global timer_thread, timer_running, timer_value

    if timer_thread is not None and timer_thread.is_alive():
        timer_value = 0
        write_timer_value(timer_value)
        timer_thread = threading.Thread(target=update_timer)
        timer_running = False
        timer_thread = None  # Stop the timer thread

    return 'Timer stopped'

@app.route('/timer/speed', methods=['POST'])
def update_timer_speed():
    global speed
    change = float(request.form['change'])  # Get the change in timer speed from the request
    speed += change
    return 'Timer speed updated'

@app.route('/timer/reset-speed', methods=['POST'])
def reset_timer_speed():
    global speed
    speed = 1
    return 'Timer speed reset'

@app.route('/timer/value', methods=['GET'])
def get_timer_value():
    return str(read_timer_value())

@app.route('/timer/get-speed', methods=['GET'])
def get_timer_speed():
    global speed
    return str(speed)

@app.route('/timer/pause', methods=['POST'])
def pause_timer():
    global timer_thread, timer_running

    if timer_thread is not None and timer_thread.is_alive() and timer_running:
        timer_running = False
        return 'Timer paused'
    else:
        return 'Timer is not running or already paused'

@app.route('/timer/continue', methods=['POST'])
def continue_timer():
    global timer_thread, timer_running

    if timer_thread is not None and not timer_thread.is_alive() and not timer_running:
        timer_running = True
        timer_thread = threading.Thread(target=update_timer)
        timer_thread.daemon = True
        timer_thread.start()
        return 'Timer continued'
    else:
        return 'Timer is already running or not paused'
@app.route('/timer/pause-state', methods=['GET'])
def get_pause_state():
    global timer_running
    return jsonify(timer_running)

@app.route('/')
def index():
    return render_template('index.html')
if __name__ == '__main__':
    if romy == False:
        turn_on_api()
        start_scripts()
        atexit.register(cleanup)
    signal.signal(signal.SIGINT, handle_interrupt)
    app.run(host='0.0.0.0', port=8000)
# gychf