from flask import Flask, render_template, request, redirect, jsonify
import json
import paramiko
import atexit
import os
from dotenv import load_dotenv
import time
import requests
import subprocess
import signal
import sys
import threading
load_dotenv()
app = Flask(__name__)
command = 'python relay_control.py'
ssh = None
stdin = None
pi2 = None
romy = True
fade_duration = 3  # Fade-out duration in seconds
fade_interval = 0.1  # Interval between volume adjustments in seconds
fade_steps = int(fade_duration / fade_interval)  # Number of fade steps
sensor_1_triggered = False
sensor_2_triggered = False
ip1home = '192.168.1.19'
ip1brink = '192.168.0.104'
ip2home = '192.168.1.28'
ip2brink = '192.168.0.105'
active_ssh_connections = {}

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def turn_on_api():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip1brink, username=os.getenv("SSH_USERNAME"), password=os.getenv("SSH_PASSWORD"))
    ssh.exec_command('python status.py')
    establish_ssh_connection()

def establish_ssh_connection():
    global ssh, stdin
    
    if ssh is None or not ssh.get_transport().is_active():
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip1brink, username=os.getenv("SSH_USERNAME"), password=os.getenv("SSH_PASSWORD"))
        stdin = ssh.exec_command(command)[0]
    
    global pi2
    
    if pi2 is None or not pi2.get_transport().is_active():
        pi2 = paramiko.SSHClient()
        pi2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        pi2.connect(ip2brink, username=os.getenv("SSH_USERNAME"), password=os.getenv("SSH_PASSWORD"))

# Function to execute the delete-locks.py script
def execute_delete_locks_script():
    ssh.exec_command('python delete-locks.py')

def start_scripts():
    pi2.exec_command('python status.py')
    pi2.exec_command('python sensor_board.py')
    pi2.exec_command('python ir.py')
    # pi2.exec_command('python distort.py')
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

@app.route('/retriever')
def retriever():
    return render_template('retriever.html')
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

@app.route('/pin-info')
def pin_info():
    return render_template('pin_info.html')
# Global variable to keep track of the currently playing music file
current_file = None

@app.route('/get_played_music_status', methods=['GET'])
def get_played_music_status():
    global current_file

    if current_file:
        file_data = [{'filename': current_file, 'status': 'playing'}]
    else:
        file_data = []

    return jsonify(file_data)

@app.route('/pause_music', methods=['POST'])
def pause_music():
    selected_file = request.form['file']
    soundcard_channel = request.form['channel']  # Get the soundcard channel from the AJAX request
    if selected_file:
        # Fade out the music gradually
        fade_duration = 2  # Adjust the fade duration as needed
        fade_interval = 0.1  # Adjust the fade interval as needed
        max_volume = 25
                # Update the status in the JSON file to "paused"
        file_path = os.path.join(current_dir, 'json', 'file_status.json')
        with open(file_path, 'r') as file:
            file_data = json.load(file)

        for entry in file_data:
            if entry['filename'] == selected_file and entry['soundcard_channel'] == soundcard_channel:
                entry['status'] = 'paused'
                break

        with open(file_path, 'w') as file:
            json.dump(file_data, file)
        # Calculate the step size for volume reduction
        step_size = max_volume / (fade_duration / fade_interval)
            # Extract the first number after "hw"
        import re
        match = re.search(r'hw:(\d+)', soundcard_channel)
        if match:
            soundcard_number = match.group(1)
        else:
            return 'Invalid soundcard channel'
        # Get the process ID of the mpg123 process
        command = f'pgrep -f "mpg123 -a {soundcard_channel} Music/{selected_file}"'
        stdin, stdout, stderr = pi2.exec_command(command)
        process_id = stdout.read().decode().strip()

        if process_id:
            # Reduce the volume gradually
            for volume in reversed(range(0, max_volume, int(step_size))):
                command = f'amixer -c {soundcard_number} set PCM Playback Volume {volume}%'
                pi2.exec_command(command)
                time.sleep(fade_interval)

                # Check if the volume reached 0
                if volume <= 0:
                    # Pause the music by sending a SIGSTOP signal to the mpg123 process
                    command = f'pkill -STOP -f "mpg123 Music/{selected_file}"'
                    pi2.exec_command(command)

            return f'Music paused for {selected_file} on pi2'
        else:
            return f'{selected_file} is not currently playing'
    else:
        return 'No file selected to pause'

@app.route('/resume_music', methods=['POST'])
def resume_music():
    selected_file = request.form['file']
    soundcard_channel = request.form['channel']
    if selected_file:
        # Fade in the music gradually
        fade_duration = 2  # Adjust the fade duration as needed
        fade_interval = 0.1  # Adjust the fade interval as needed
        target_volume = 25  # Adjust the desired volume level
        file_path = os.path.join(current_dir, 'json', 'file_status.json')
        with open(file_path, 'r') as file:
            file_data = json.load(file)

        for entry in file_data:
            if entry['filename'] == selected_file and entry['soundcard_channel'] == soundcard_channel:
                entry['status'] = 'playing'
                break

        with open(file_path, 'w') as file:
            json.dump(file_data, file)
        import re
        match = re.search(r'hw:(\d+)', soundcard_channel)
        if match:
            soundcard_number = match.group(1)
        else:
            return 'Invalid soundcard channel'
        # Calculate the step size for volume increase
        step_size = target_volume / (fade_duration / fade_interval)

        # Get the process ID of the mpg123 process
        command = f'pgrep -f "mpg123 -a {soundcard_channel} Music/{selected_file}"'
        stdin, stdout, stderr = pi2.exec_command(command)
        process_id = stdout.read().decode().strip()

        if process_id:
            # Increase the volume gradually
            for volume in range(0, target_volume + 1, int(step_size)):
                # Set the same volume for both Front Left and Front Right channels
                command = f'amixer -c {soundcard_number} set PCM Playback Volume {volume}%'
                pi2.exec_command(command)
                time.sleep(fade_interval)
            print(selected_file)
            command = f'pkill -CONT -f "mpg123 Music/{selected_file}"'
            pi2.exec_command(command)

            return 'Music resumed on pi2'
        else:
            return 'No music is currently playing'
    else:
        return 'No music is currently playing'


current_dir = os.path.abspath(os.path.dirname(__file__))

@app.route('/play_music_garage_alley', methods=['POST'])
def play_music_garage_alley():
    global current_file
    selected_file = request.form['file']
    current_file = selected_file

    # Define the soundcard channel information
    soundcard_channel = 'hw:3,0'  # Adjust this based on your specific configuration

    # Construct the command to play the music using the specified soundcard channel
    command = f'mpg123 -a {soundcard_channel} Music/{selected_file} &'
    pi2.exec_command(command)

    # Save the data to a JSON file on the server
    status = 'playing'
    data = {'filename': selected_file, 'status': status, 'soundcard_channel': soundcard_channel}
    file_path = os.path.join(current_dir, 'json', 'file_status.json')

    # Ensure the directory exists or create it if not
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    try:
        # Load existing data from the JSON file (if it exists)
        with open(file_path, 'r') as file:
            file_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        file_data = []

    # Append the new data to the existing data
    file_data.append(data)

    # Write the data to the JSON file
    with open(file_path, 'w') as file:
        json.dump(file_data, file)

    print("Data written successfully.")

    return 'Music started on pi2'

@app.route('/play_music_garden', methods=['POST'])
def play_music_garden():
    global current_file
    selected_file = request.form['file']
    current_file = selected_file

    # Define the soundcard channel information
    soundcard_channel = 'hw:2,0'  # Adjust this based on your specific configuration

    # Construct the command to play the music using the specified soundcard channel
    command = f'mpg123 -a {soundcard_channel} Music/{selected_file} &'
    pi2.exec_command(command)

    # Save the data to a JSON file on the server
    status = 'playing'
    data = {'filename': selected_file, 'status': status, 'soundcard_channel': soundcard_channel}
    file_path = os.path.join(current_dir, 'json', 'file_status.json')

    # Ensure the directory exists or create it if not
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    try:
        # Load existing data from the JSON file (if it exists)
        with open(file_path, 'r') as file:
            file_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        file_data = []

    # Append the new data to the existing data
    file_data.append(data)

    # Write the data to the JSON file
    with open(file_path, 'w') as file:
        json.dump(file_data, file)

    print("Data written successfully.")

    return 'Music started on pi2'

@app.route('/get_file_status', methods=['GET'])
def get_file_status():
    file_path = os.path.join(current_dir, 'json', 'file_status.json')
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                file_data = json.load(file)
            return jsonify(file_data)
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify([])
    else:
        return jsonify([])

@app.route('/play_music_lab', methods=['POST'])
def play_music_lab():
    global current_file
    selected_file = request.form['file']
    current_file = selected_file

    # Define the soundcard channel information
    soundcard_channel = 'hw:1,0'  # Adjust this based on your specific configuration

    # Construct the command to play the music using the specified soundcard channel
    command = f'mpg123 -a {soundcard_channel} Music/{selected_file} &'
    pi2.exec_command(command)

    # Save the data to a JSON file on the server
    status = 'playing'
    data = {'filename': selected_file, 'status': status, 'soundcard_channel': soundcard_channel}
    file_path = os.path.join(current_dir, 'json', 'file_status.json')

    # Ensure the directory exists or create it if not
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    try:
        # Load existing data from the JSON file (if it exists)
        with open(file_path, 'r') as file:
            file_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        file_data = []

    # Append the new data to the existing data
    file_data.append(data)

    # Write the data to the JSON file
    with open(file_path, 'w') as file:
        json.dump(file_data, file)

    print("Data written successfully.")

    return 'Music started on pi2'

# @app.route('/play_music_all', methods=['POST'])
# def play_music_all():
#     global current_file
#     selected_file = request.form['file']
#     current_file = selected_file

#     # Define the soundcard channel information
#     soundcard_channel1 = 'hw:1,0'  # Adjust this based on your specific configuration
#     soundcard_channel2 = 'hw:2,0'  # Adjust this based on your specific configuration
#     # Construct the command to play the music using the specified soundcard channel
#     command1 = f'mpg123 -a {soundcard_channel1} Music/{selected_file} &'
#     command2 = f'mpg123 -a {soundcard_channel2} Music/{selected_file} &'

#     print("Sending command1...")
#     pi2.exec_command(command1)
#     print("Command1 executed successfully.")

#     # Remove time.sleep(2) if present

#     print("Sending command2...")
#     pi2.exec_command(command2)
#     print("Command2 executed successfully.")

#     # Save the data to a JSON file on the server
#     status = 'playing'
#     data = {'filename': selected_file, 'status': status, 'soundcard_channel': soundcard_channel1}
#     file_path = os.path.join(current_dir, 'json', 'file_status.json')

#     directory = os.path.dirname(file_path)
#     if not os.path.exists(directory):
#         os.makedirs(directory)

#     try:
#         # Load existing data from the JSON file (if it exists)
#         with open(file_path, 'r') as file:
#             file_data = json.load(file)
#     except (FileNotFoundError, json.JSONDecodeError):
#         file_data = []

#     # Append the new data to the existing data
#     file_data.append(data)

#     # Write the data to the JSON file
#     with open(file_path, 'w') as file:
#         json.dump(file_data, file)
#     data = {'filename': selected_file, 'status': status, 'soundcard_channel': soundcard_channel2}
#     file_path = os.path.join(current_dir, 'json', 'file_status.json')

#     # Ensure the directory exists or create it if not
#     directory = os.path.dirname(file_path)
#     if not os.path.exists(directory):
#         os.makedirs(directory)

#     try:
#         # Load existing data from the JSON file (if it exists)
#         with open(file_path, 'r') as file:
#             file_data = json.load(file)
#     except (FileNotFoundError, json.JSONDecodeError):
#         file_data = []

#     # Append the new data to the existing data
#     file_data.append(data)

#     # Write the data to the JSON file
#     with open(file_path, 'w') as file:
#         json.dump(file_data, file)

#     print("Data written successfully.")

#     return 'Music started on pi2'

@app.route('/stop_music', methods=['POST'])
def stop_music():
    # Stop the music on pi2
    stdin, stdout, stderr = pi2.exec_command('pkill -9 mpg123')

    # Wipe the entire JSON file by overwriting it with an empty list
    file_path = os.path.join(current_dir, 'json', 'file_status.json')
    with open(file_path, 'w') as file:
        json.dump([], file)

    return 'Music stopped on pi2 and JSON wiped.'

@app.route('/backup-top-pi', methods=['POST'])
def backup_top_pi():
    ssh.exec_command('./commit_and_push.sh')
    return "Top pi backed up"

@app.route('/backup-middle-pi', methods=['POST'])
def backup_middle_pi():
    ssh.exec_command('./commit_and_push.sh')
    return "Middle pi backed up"
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


API_URL = 'http://192.168.0.105:5001/current_state'

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
    pi2.exec_command('pkill -f distort.py')
    pi2.exec_command('pkill -f sensor_board.py')
    pi2.exec_command('pkill -f ir.py')
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
    global ssh, stdin
    ssh.exec_command('sudo reboot')
    ssh.close()
    time.sleep(40)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip1brink, username=os.getenv("SSH_USERNAME"), password=os.getenv("SSH_PASSWORD"))
    time.sleep(2)
    ssh.exec_command('python status.py')
    time.sleep(2)
    stdin = ssh.exec_command(command)[0]
    time.sleep(3)
    ssh.exec_command('python delete-locks.py')
    ssh.exec_command('python read.py')
    ssh.exec_command('python keypad.py')
    return "top pi reset succesfully!"

@app.route('/reboot-music-pi', methods=['POST'])
def reboot_music_pi():
    global pi2
    pi2.exec_command('sudo reboot')
    pi2.close()
    time.sleep(40)
    pi2 = paramiko.SSHClient()
    pi2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pi2.connect(ip2brink, username=os.getenv("SSH_USERNAME"), password=os.getenv("SSH_PASSWORD"))
    time.sleep(3)
    pi2.exec_command('python status.py')
    pi2.exec_command('python sensor_board.py')
    pi2.exec_command('python ir.py')
    return "middle pi reset succesfully!"


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

@app.route('/get-pi-status', methods=['GET'])
def get_pi_status():
    global ssh, pi2

    # Prepare a list of dictionaries containing IP and SSH status for each Pi
    pi_statuses = []

    if ssh:
        pi1_status = {"ip_address": ip1brink}
        try:
            if ssh.get_transport().is_active():
                pi1_status["ssh_active"] = "Online"
        except AttributeError:
            pi1_status["ssh_active"] = "Offline"
        pi_statuses.append(pi1_status)

    if pi2:
        pi2_status = {"ip_address": ip2brink}
        try:
            if pi2.get_transport().is_active():
                pi2_status["ssh_active"] = "Online"
        except AttributeError:
            pi2_status["ssh_active"] = "Offline"
        pi_statuses.append(pi2_status)

    # Render the template fragment and return as JSON
    return jsonify(render_template('status_table_fragment.html', pi_statuses=pi_statuses))


@app.route('/')
def index():
    return render_template('index.html')
if __name__ == '__main__':
    if romy == False:
        turn_on_api()
        start_scripts()
        atexit.register(cleanup)
    signal.signal(signal.SIGINT, handle_interrupt)
    app.run(host='0.0.0.0', port=80)