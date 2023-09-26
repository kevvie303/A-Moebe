from flask import Flask, render_template, request, redirect, jsonify, url_for
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import paramiko
import atexit
import os
from dotenv import load_dotenv
import time
import multiprocessing
import requests
import subprocess
import signal
import sys
import threading
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import paho.mqtt.client as mqtt
load_dotenv()
app = Flask(__name__)
#command = 'python relay_control.py'
ssh = None
stdin = None
pi2 = None
pi3 = None
romy = False
aborted = False
fade_duration = 3  # Fade-out duration in seconds
fade_interval = 0.1  # Interval between volume adjustments in seconds
fade_steps = int(fade_duration / fade_interval)  # Number of fade steps
sensor_1_triggered = False
sensor_2_triggered = False
ip1home = '192.168.1.19'
ip1brink = '192.168.0.104'
ip2home = '192.168.1.28'
ip2brink = '192.168.0.105'
ip3brink = '192.168.0.114'
sequence = 0
should_sound_play = True
code1 = False
code2 = False
code3 = False
#logging.basicConfig(level=logging.DEBUG)  # Use appropriate log level
active_ssh_connections = {}
CORS(app)
scheduler = BackgroundScheduler()
scheduler.start()
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def turn_on_api():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip1brink, username=os.getenv("SSH_USERNAME"), password=os.getenv("SSH_PASSWORD"))
    ssh.exec_command('sudo -E python status.py')
    establish_ssh_connection()

def establish_ssh_connection():
    global ssh, stdin
    
    if ssh is None or not ssh.get_transport().is_active():
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip1brink, username=os.getenv("SSH_USERNAME"), password=os.getenv("SSH_PASSWORD"))
        
    
    global pi2
    
    if pi2 is None or not pi2.get_transport().is_active():
        pi2 = paramiko.SSHClient()
        pi2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        pi2.connect(ip2brink, username=os.getenv("SSH_USERNAME"), password=os.getenv("SSH_PASSWORD"))
    global pi3
    if pi3 is None or not pi3.get_transport().is_active():
        pi3 = paramiko.SSHClient()
        pi3.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        pi3.connect(ip3brink, username=os.getenv("SSH_USERNAME"), password=os.getenv("SSH_PASSWORD"))
broker_ip = "192.168.0.103"  # IP address of the broker Raspberry Pi

# Define the topic prefix to subscribe to (e.g., "sensor_state/")
prefix_to_subscribe = "sensor_state/"

# Callback function to process incoming MQTT messages
def on_message(client, userdata, message):
    # Extract the topic and message payload
    topic = message.topic
    sensor_name = topic[len(prefix_to_subscribe):]  # Extract sensor name from the topic
    sensor_state = message.payload.decode("utf-8")

    # Process the received sensor state as needed
    print(f"Received sensor state for {sensor_name}: {sensor_state}")

# Create an MQTT client instance
client = mqtt.Client()

# Set the callback function for incoming MQTT messages
client.on_message = on_message

# Connect to the MQTT broker
client.connect(broker_ip, 1883)

# Subscribe to all topics under the specified prefix
client.subscribe(prefix_to_subscribe + "#")  # Subscribe to all topics under the prefix
# Function to execute the delete-locks.py script
mqtt_thread = threading.Thread(target=client.loop_forever)
mqtt_thread.start()
def execute_delete_locks_script():
    ssh.exec_command('python delete-locks.py')

@app.route('/trigger', methods=['POST'])
def trigger():
    # Process the data and respond as needed
    return jsonify({'message': 'Data received successfully'})
@app.route('/retriever')
def retriever():
    return render_template('retriever.html')
def start_scripts():
    global should_sound_play
    #pi2.exec_command('python sensor_board.py')
    pi2.exec_command('sudo python sinus_game.py')
    # pi2.exec_command('python distort.py')
    #ssh.exec_command('python read.py')
    # ssh.exec_command('python keypad.py')
    #pi3.exec_command('python ir.py')
    sensor_thread.start()
    pi2.exec_command('python status.py')
    time.sleep(0.5)
    pi3.exec_command('python status.py')
    time.sleep(0.5)
    #scheduler.add_job(monitor_sensor_statuses, 'interval', seconds=0.1)

@app.route('/add_music1', methods=['POST'])
def add_music1():
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

                sftp = pi3.open_sftp()
                
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
        for entry in file_data:
            if entry['filename'] == selected_file and entry['soundcard_channel'] == soundcard_channel:
                pi_name = entry['pi']
                break
        else:
            return 'Selected song not found in the JSON file'
        
        if pi_name == 'pi2':
            pi = pi2
        elif pi_name == 'pi3':
            pi = pi3
            max_volume = 85
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
        stdin, stdout, stderr = pi.exec_command(command)
        process_id = stdout.read().decode().strip()

        if process_id:
            # Reduce the volume gradually
            for volume in reversed(range(0, max_volume, int(step_size))):
                command = f'amixer -c {soundcard_number} set PCM Playback Volume {volume}%'
                pi.exec_command(command)
                time.sleep(fade_interval)

                # Check if the volume reached 0
                if volume <= 0:
                    # Pause the music by sending a SIGSTOP signal to the mpg123 process
                    command = f'pkill -STOP -f "mpg123 Music/{selected_file}"'
                    pi.exec_command(command)

            return f'Music paused for {selected_file} on {pi}'
        else:
            return f'{selected_file} is not currently playing'
    else:
        return 'No file selected to pause'
@app.route('/fade_music_out', methods=['POST'])
def fade_music_out():

        # Gradually reduce the volume from 80 to 40
    for volume in range(75, 15, -1):
        # Send the volume command to the Raspberry Pi
        command = f'echo "volume {volume}" | sudo tee /tmp/mpg123_fifo'
        stdin, stdout, stderr = pi3.exec_command(command)

        # Wait for a short duration between volume changes
        time.sleep(0.05)  # Adjust the sleep duration as needed
    return "Volume faded successfully"
@app.route('/fade_music_in', methods=['POST'])
def fade_music_in():

        # Gradually reduce the volume from 80 to 40
    for volume in range(15, 75, 1):
        # Send the volume command to the Raspberry Pi
        command = f'echo "volume {volume}" | sudo tee /tmp/mpg123_fifo'
        stdin, stdout, stderr = pi3.exec_command(command)

        # Wait for a short duration between volume changes
        time.sleep(0.05)  # Adjust the sleep duration as needed
    return "Volume faded successfully"
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
        for entry in file_data:
            if entry['filename'] == selected_file and entry['soundcard_channel'] == soundcard_channel:
                pi_name = entry['pi']
                break
        else:
            return 'Selected song not found in the JSON file'
        if pi_name == 'pi2':
            pi = pi2
        elif pi_name == 'pi3':
            pi = pi3
            target_volume = 85
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
        stdin, stdout, stderr = pi.exec_command(command)
        process_id = stdout.read().decode().strip()

        if process_id:
            # Increase the volume gradually
            for volume in range(0, target_volume + 1, int(step_size)):
                # Set the same volume for both Front Left and Front Right channels
                command = f'amixer -c {soundcard_number} set PCM Playback Volume {volume}%'
                pi.exec_command(command)
                time.sleep(fade_interval)
            print(selected_file)
            command = f'pkill -CONT -f "mpg123 Music/{selected_file}"'
            pi.exec_command(command)

            return f'Music resumed on {pi}'
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
    pi = 'pi2'
    # Define the soundcard channel information
    soundcard_channel = 'hw:4,0'  # Adjust this based on your specific configuration
    # Construct the command to play the music using the specified soundcard channel
    command = f'mpg123 -a {soundcard_channel} Music/{selected_file} &'
    pi2.exec_command(command)

    # Save the data to a JSON file on the server
    status = 'playing'
    data = {'filename': selected_file, 'status': status, 'soundcard_channel': soundcard_channel, 'pi': pi}
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
    pi = 'pi3'
    print(selected_file)
    # Define the soundcard channel information
    soundcard_channel = 'hw:0,0'  # Adjust this based on your specific configuration
    # Create a new FIFO file
    if "Ambience" in selected_file:
        load_command = f'echo "load /home/pi/Music/{current_file}" | sudo tee /tmp/mpg123_fifo'
        print(current_file)
        pi3.exec_command(load_command)
        print(load_command)
    else:
        command = f'mpg123 -a {soundcard_channel} Music/{current_file} &'
        pi3.exec_command(command)
        print("hiii")
    # Command to play the music using the specified soundcard channel


    # Send the load command to the FIFO file


    # Save the data to a JSON file on the server
    status = 'playing'
    data = {'filename': selected_file, 'status': status, 'soundcard_channel': soundcard_channel, 'pi': pi}
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
    
@app.route('/get_task_status', methods=['GET'])
def get_task_status():
    file_path = os.path.join(current_dir, 'json', 'tasks.json')
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                file_data = json.load(file)
            return jsonify(file_data)
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify([])
    else:
        return jsonify([])
    
@app.route('/solve_task/<task_name>', methods=['POST'])
def solve_task(task_name):
    file_path = os.path.join(current_dir, 'json', 'tasks.json')

    try:
        with open(file_path, 'r') as file:
            tasks = json.load(file)

        for task in tasks:
            if task['task'] == task_name:
                task['state'] = 'solved'

        with open(file_path, 'w') as file:
            json.dump(tasks, file, indent=4)
        with app.app_context():
            return jsonify({'message': 'Task updated successfully'})
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({'message': 'Error updating task'})
    
@app.route('/pend_task/<task_name>', methods=['POST'])
def pend_task(task_name):
    file_path = os.path.join(current_dir, 'json', 'tasks.json')

    try:
        with open(file_path, 'r') as file:
            tasks = json.load(file)

        for task in tasks:
            if task['task'] == task_name:
                task['state'] = 'pending'

        with open(file_path, 'w') as file:
            json.dump(tasks, file, indent=4)

        return jsonify({'message': 'Task updated successfully'})
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({'message': 'Error updating task'})
@app.route('/reset_task_statuses', methods=['POST'])
def reset_task_statuses():
    global sequence
    file_path = os.path.join(current_dir, 'json', 'tasks.json')
    sequence = 0
    try:
        with open(file_path, 'r') as file:
            tasks = json.load(file)

        for task in tasks:
            task['state'] = 'pending'

        with open(file_path, 'w') as file:
            json.dump(tasks, file, indent=4)

        return jsonify({'message': 'Task statuses reset successfully'})
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({'message': 'Error resetting task statuses'})
@app.route('/reset_puzzles', methods=['POST'])
def reset_puzzles():
    global aborted
    global code1
    global code2
    global code3
    aborted = True
    code1 = False
    code2 = False
    code3 = False
    update_snooze_status(False)
    pi3.exec_command('raspi-gpio set 16 op dl')
    pi2.exec_command('sudo pkill -f sinus_game.py')
    pi2.exec_command('pkill -f sensor_board.py')
    pi2.exec_command('pkill -9 mpg123')
    pi2.exec_command('raspi-gpio set 12 op dl')
    pi2.exec_command('raspi-gpio set 1 op dl')
    pi2.exec_command('raspi-gpio set 7 op dl')
    pi2.exec_command('raspi-gpio set 8 op dl')
    time.sleep(3)
    pi2.exec_command('sudo python sinus_game.py')
    #pi2.exec_command('python sensor_board.py')
    time.sleep(15)
    aborted = False
    return "puzzles reset"

def read_snooze_status():
    with open('json/snoozeStatus.json', 'r') as file:
        data = json.load(file)
    return data.get('snoozed', False)

# Function to update the snooze status in the JSON file
def update_snooze_status(snoozed):
    data = {"snoozed": snoozed}
    with open('json/snoozeStatus.json', 'w') as file:
        json.dump(data, file)

@app.route('/get_snooze_status', methods=['GET'])
def get_snooze_status():
    snooze_status = read_snooze_status()
    return {"snoozed": snooze_status}

@app.route('/wake_room', methods=['POST'])
def wake_room():
    # Update the snooze status to 'false'
    pi3.exec_command('raspi-gpio set 12 op dl \n raspi-gpio set 7 op dl \n raspi-gpio set 1 op dl \n raspi-gpio set 8 op dl')
    #pi3.exec_command('raspi-gpio set 7 op dl')
    #pi3.exec_command('raspi-gpio set 1 op dl')
    #pi3.exec_command('raspi-gpio set 8 op dl')
    update_snooze_status(False)
    return "room awakened"

@app.route('/snooze_game', methods=['POST'])
def snooze_game():
    light1off = 'raspi-gpio set 12 op dh'
    light2off = 'raspi-gpio set 7 op dh'
    light3off = 'raspi-gpio set 1 op dh'
    light4off = 'raspi-gpio set 8 op dh'
    lightsoff = f"{light1off}; {light2off}; {light3off}; {light4off}"
    pi3.exec_command(lightsoff)
    ssh.exec_command('raspi-gpio set 17 op dh')
    ssh.exec_command('raspi-gpio set 27 op dh')
    pi3.exec_command('raspi-gpio set 16 op dh')
    pi3.exec_command('raspi-gpio set 25 op dh')
    update_snooze_status(True)
    return "room snoozed"
@app.route('/add_task', methods=['POST'])
def add_task():
    file_path = os.path.join(current_dir, 'json', 'tasks.json')
    task_data = request.get_json()

    try:
        with open(file_path, 'r') as file:
            tasks = json.load(file)
        
        tasks.append(task_data)

        with open(file_path, 'w') as file:
            json.dump(tasks, file, indent=4)

        return jsonify({'message': 'Task added successfully'})
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({'message': 'Error adding task'})
    
@app.route('/remove_task', methods=['POST'])
def remove_task():
    file_path = os.path.join(current_dir, 'json', 'tasks.json')
    task_data = request.get_json()

    try:
        with open(file_path, 'r') as file:
            tasks = json.load(file)

        updated_tasks = [task for task in tasks if task['task'] != task_data['task']]

        with open(file_path, 'w') as file:
            json.dump(updated_tasks, file, indent=4)

        return jsonify({'message': f'Task "{task_data["task"]}" removed successfully'})
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({'message': 'Error removing task'})
@app.route('/edit_task', methods=['POST'])
def edit_task():
    file_path = os.path.join(current_dir, 'json', 'tasks.json')
    edit_data = request.get_json()

    try:
        with open(file_path, 'r') as file:
            tasks = json.load(file)

        # Find the task to edit by its name
        for task in tasks:
            if task['task'] == edit_data['task']:
                task['task'] = edit_data['editedTaskName']
                task['description'] = edit_data['editedTaskDescription']

        # Write the updated task list back to the JSON file
        with open(file_path, 'w') as file:
            json.dump(tasks, file, indent=4)

        return jsonify({'message': 'Task updated successfully'})
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({'message': 'Error updating task'})
    
@app.route('/get_tasks', methods=['GET'])
def get_tasks():
    file_path = os.path.join(current_dir, 'json', 'tasks.json')
    
    try:
        with open(file_path, 'r') as file:
            tasks = json.load(file)
        return jsonify(tasks)
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify([])
    
@app.route('/play_music_lab', methods=['POST'])
def play_music_lab():
    global current_file
    selected_file = request.form['file']
    current_file = selected_file
    pi = "pi2"

    # Define the soundcard channel information
    soundcard_channel = 'hw:1,0'  # Adjust this based on your specific configuration

    # Construct the command to play the music using the specified soundcard channel
    command = f'mpg123 -a {soundcard_channel} Music/{selected_file} &'
    pi2.exec_command(command)

    # Save the data to a JSON file on the server
    status = 'playing'
    data = {'filename': selected_file, 'status': status, 'soundcard_channel': soundcard_channel, 'pi': pi}
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
def set_starting_volume(soundcard_channel):
    command = f'amixer -c {soundcard_channel} set PCM Playback Volume 25%'
    pi2.exec_command(command)
    return "Volume set to 25%"
@app.route('/stop_music', methods=['POST'])
def stop_music():
    # Stop the music on pi2
    stdin, stdout, stderr = pi2.exec_command('pkill -9 mpg123')
    stdin, stdout, stderr = pi3.exec_command('pkill -9 mpg123')
    # Wipe the entire JSON file by overwriting it with an empty list
    file_path = os.path.join(current_dir, 'json', 'file_status.json')
    with open(file_path, 'w') as file:
        json.dump([], file)

    return 'Music stopped on pi2/pi3 and JSON wiped.'

@app.route('/backup-top-pi', methods=['POST'])
def backup_top_pi():
    ssh.exec_command('./commit_and_push.sh')
    return "Top pi backed up"

@app.route('/backup-middle-pi', methods=['POST'])
def backup_middle_pi():
    ssh.exec_command('./commit_and_push.sh')
    return "Middle pi backed up"

@app.route('/lock_entrance_door', methods=['POST'])
def lock_entrance_door():
    ssh.exec_command("raspi-gpio set 17 dl")
    return "locked door"
def control_maglock():
    maglock = request.form.get('maglock')
    action = request.form.get('action')
    
    if maglock == "entrance-door-lock":
        if action == "locked":
            pi3.exec_command("raspi-gpio set 25 dl")
            return 'Maglock entrance-door-lock is now locked'
        elif action == "unlocked":
            pi3.exec_command("raspi-gpio set 25 dh")
            return 'Maglock entrance-door-lock is now unlocked'
    elif maglock == "doghouse-lock":
        if action == "locked":
            ssh.exec_command("raspi-gpio set 27 dl")
            return 'Maglock doghouse-lock is now locked'
        elif action == "unlocked":
            ssh.exec_command("raspi-gpio set 27 dh")
            return 'Maglock doghouse-lock is now unlocked'
    elif maglock == "shed-door-lock":
        if action == "locked":
            pi3.exec_command("raspi-gpio set 16 dl")
            return 'shed locked'
        elif action == "unlocked":
            pi3.exec_command("raspi-gpio set 16 dh")
            return 'shed unlocked'
    elif maglock == "blacklight":
        if action == "locked":
            ssh.exec_command("raspi-gpio set 17 dl")
            return 'blacklight locked'
        elif action == "unlocked":
            ssh.exec_command("raspi-gpio set 17 dh")
            return 'blacklight unlocked'
    elif maglock == "exit-door-lock":
        if action == "locked":
            ssh.exec_command("raspi-gpio set 21 dl")
            return 'blacklight locked'
        elif action == "unlocked":
            ssh.exec_command("raspi-gpio set 21 dh")
            return 'exit unlocked'
    elif maglock == "lab-hatch-lock":
        if action == "locked":
            ssh.exec_command("raspi-gpio set 20 dl")
            return 'blacklight locked'
        elif action == "unlocked":
            ssh.exec_command("raspi-gpio set 20 dh")
            return 'exit unlocked'
    elif maglock == "sliding-door-lock":
        if action == "locked":
            ssh.exec_command("raspi-gpio set 16 dl")
            return 'blacklight locked'
        elif action == "unlocked":
            ssh.exec_command("raspi-gpio set 16 dh")
            return 'exit unlocked'
    else:
        return 'Invalid maglock or action'

@app.route('/control_maglock', methods=['POST'])
def control_maglock_route():
    return control_maglock()



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

API_URL_SENSORS = 'http://192.168.0.104:5000/sensor/status/'
def get_sensor_status(sensor_number):
    try:
        response = requests.get(API_URL_SENSORS + str(sensor_number))
        if response.status_code == 200:
            return response.json().get('status')
        else:
            return 'unknown'
    except requests.exceptions.RequestException:
        return 'unknown'
    
API_URL_SHED_KEYPAD = 'http://192.168.0.104:5000/keypad/pressed_keys'

def get_shed_keypad_code():
    try:
        response = requests.get(API_URL_SHED_KEYPAD)
        if response.status_code == 200:
            pressed_keys_arrays = response.json().get('pressed_keys_arrays')
            if pressed_keys_arrays:
                # Get the last-used code from the array
                last_used_code_array = pressed_keys_arrays[-1]
                last_used_code = ''.join(last_used_code_array)
                return last_used_code
            else:
                return 'No code entered yet'
        else:
            return 'unknown'
    except requests.exceptions.RequestException:
        return 'unknown'

API_URL_SENSORS_PI2 = 'http://192.168.0.105:5001/sensor/status/'

def get_sensor_status_pi2(sensor_number):
    try:
        response = requests.get(API_URL_SENSORS_PI2 + str(sensor_number))
        if response.status_code == 200:
            return response.json().get('status')
        else:
            return 'unknown'
    except requests.exceptions.RequestException:
        return 'unknown'
with open('json/sensor_data.json', 'r') as json_file:
    sensors = json.load(json_file)
def monitor_sensor_statuses():
    global sequence
    global code1
    global code2
    global code3
    while True:
        green_house_ir_status = get_ir_sensor_status(14)
        red_house_ir_status = get_ir_sensor_status(20)
        blue_house_ir_status = get_ir_sensor_status(18)
        entrance_door_status = get_sensor_status(14)
        sinus_status = get_sinus_status()
        top_left_kraken = get_sensor_status_pi2(15)
        bottom_left_kraken = get_sensor_status_pi2(16)
        top_right_kraken = get_sensor_status_pi2(20)
        bottom_right_kraken = get_sensor_status_pi2(23)
        last_used_keypad_code = get_shed_keypad_code()
        #print(last_used_keypad_code)
        if last_used_keypad_code == "1527" and code1 == False:
            code1 = True
            ssh.exec_command("raspi-gpio set 1 op dh")
            time.sleep(1)
            ssh.exec_command("raspi-gpio set 1 op dl")
        if (last_used_keypad_code == "7867" or last_used_keypad_code == "8978") and code2 == False:
            code2 = True
            ssh.exec_command("raspi-gpio set 1 op dh")
            time.sleep(1)
            ssh.exec_command("raspi-gpio set 1 op dl")
        if last_used_keypad_code == "0129" and code3 == False:
            code3 = True
            ssh.exec_command("raspi-gpio set 1 op dh")
            time.sleep(1)
            ssh.exec_command("raspi-gpio set 1 op dl")
        if code1 and code2 and code3:
            print("executed")
            pi3.exec_command('raspi-gpio set 16 op dh')
            code1 = False
            code2 = False
            code3 = False
        if top_left_kraken == "closed":
            pi2.exec_command('raspi-gpio set 12 op dh')
        else:
            pi2.exec_command('raspi-gpio set 12 op dl')
        if bottom_left_kraken == "closed":
            pi2.exec_command('raspi-gpio set 1 op dh')
        else:
            pi2.exec_command('raspi-gpio set 1 op dl')
        if top_right_kraken == "closed":
            pi2.exec_command('raspi-gpio set 7 op dh')
        else:
            pi2.exec_command('raspi-gpio set 7 op dl')
        if bottom_right_kraken == "closed":
            pi2.exec_command('raspi-gpio set 8 op dh')
        else:
            pi2.exec_command('raspi-gpio set 8 op dl')
        if sinus_status == "solved" and aborted == False:
            pi2.exec_command("mpg123 -a hw:1,0 Music/pentakill.mp3")

        if green_house_ir_status == 'active' and sequence == 0:
            pi3.exec_command("raspi-gpio set 15 op dh")
            sequence = 1
        if red_house_ir_status == 'active' and sequence == 1:
            pi3.exec_command("raspi-gpio set 21 op dh")
            sequence = 2
        elif red_house_ir_status == 'active' and sequence <= 0:
            pi3.exec_command("raspi-gpio set 21 op dh")
            time.sleep(0.5)
            pi3.exec_command("raspi-gpio set 21 op dl")
            pi3.exec_command("raspi-gpio set 15 op dl")
            sequence = 0
        if blue_house_ir_status == 'active' and sequence == 2:
            solve_task("tree-lights")
            pi3.exec_command("raspi-gpio set 23 op dh")
            fade_out_thread = threading.Thread(target=fade_music_out)
            fade_out_thread.start()
            time.sleep(1)
            pi3.exec_command("raspi-gpio set 23 op dl \n raspi-gpio set 21 op dl \n raspi-gpio set 15 op dl")
            time.sleep(1)
            pi3.exec_command("raspi-gpio set 23 op dh \n raspi-gpio set 21 op dh \n raspi-gpio set 15 op dh")
            time.sleep(1)
            pi3.exec_command("raspi-gpio set 23 op dl \n raspi-gpio set 21 op dl \n raspi-gpio set 15 op dl")
            time.sleep(1)
            pi3.exec_command("raspi-gpio set 23 op dh \n raspi-gpio set 21 op dh \n raspi-gpio set 15 op dh")
            time.sleep(1)
            pi3.exec_command("raspi-gpio set 23 op dl \n raspi-gpio set 21 op dl \n raspi-gpio set 15 op dl")
            sequence = 0
            time.sleep(1)
            pi3.exec_command("mpg123 -a hw:0,0 Music/Tree-solve.mp3")
            time.sleep(7)
            fade_in_thread = threading.Thread(target=fade_music_in)
            fade_in_thread.start()
        elif blue_house_ir_status == 'active' and sequence != 2:
            pi3.exec_command("raspi-gpio set 23 op dh")
            time.sleep(0.5)
            pi3.exec_command("raspi-gpio set 23 op dl")
            pi3.exec_command("raspi-gpio set 21 op dl")
            pi3.exec_command("raspi-gpio set 15 op dl")
            sequence = 0
        time.sleep(0.1)
# Start a new thread for monitoring sensor statuses
@app.route('/add_sensor', methods=['GET', 'POST'])
def add_sensor():
    if request.method == 'POST':
        # Retrieve form data
        name = request.form['name']
        sensor_type = request.form['type']
        pin = int(request.form['pin'])
        pi = request.form['pi']

        # Create a new sensor dictionary with an initial state of "Not triggered"
        new_sensor = {
            "name": name,
            "type": sensor_type,
            "pin": pin,
            "pi": pi,
            "state": "Not triggered"
        }

        # Add the new sensor to the list
        sensors.append(new_sensor)

        # Save the updated sensor data to the JSON file
        with open('json/sensor_data.json', 'w') as json_file:
            json.dump(sensors, json_file, indent=4)
        target_directory = '~/'
        script_path = 'json/sensor_data.json'
        target_usernames = {
            "top-pi": "pi@192.168.0.104",
            "middle-pi": "pi@192.168.0.105",
            "tree-pi": "pi@192.168.0.114"
        }

        success_message = "Script sent successfully to the following IP addresses:<br>"

        for target_ip in target_usernames.values():
            # Construct the SCP command
            scp_command = f'scp {script_path} {target_ip}:{target_directory}'

            try:
                # Execute the SCP command
                subprocess.run(scp_command, shell=True, check=True)
                success_message += f"- {target_ip}<br>"
            except subprocess.CalledProcessError as e:
                return f'Error occurred while sending script to {target_ip}: {e}'

        return redirect(url_for('list_sensors'))

    return render_template('add_sensor.html')
@app.route('/list_sensors')
def list_sensors():
    return render_template('list_sensors.html', sensors=sensors)
def start_bird_sounds():
    pi3.exec_command("mpg123 -a hw:1,0 Music/Pecker.mp3")
    print("1")
    time.sleep(8)
    pi3.exec_command("mpg123 -a hw:1,0 Music/Owl.mp3")
    print("2")
    time.sleep(8)
    pi3.exec_command("mpg123 -a hw:1,0 Music/Gull.mp3")
    print("3")


API_URL_IR_SENSORS = 'http://192.168.0.114:5001/ir-sensor/status/'

def get_ir_sensor_status(sensor_number):
    try:
        response = requests.get(API_URL_IR_SENSORS + str(sensor_number))
        if response.status_code == 200:
            return response.json().get('status')
        else:
            return 'unknown'
    except requests.exceptions.RequestException:
        return 'unknown'
sensor_thread = threading.Thread(target=monitor_sensor_statuses)
sensor_thread.daemon = True

API_URL_SINUS = 'http://192.168.0.105:5001/sinus-game/state'

def get_sinus_status():
    try:
        response = requests.get(API_URL_SINUS)
        if response.status_code == 200:
            return response.json().get('state')
        else:
            return 'unknown'
    except requests.exceptions.RequestException:
        return 'unknown'
#@app.route('/turn_on', methods=['POST'])
#def turn_on():
    maglock = request.form['maglock']
    return turn_on_maglock(maglock)

#@app.route('/turn_off', methods=['POST'])
#def turn_off():
    maglock = request.form['maglock']
    return turn_off_maglock(maglock)



def cleanup():
    pi2.exec_command('sudo pkill -f sinus_game.py')
    execute_delete_locks_script()
    ssh.exec_command('pkill -f status.py')
    pi2.exec_command('pkill -f status.py')
    pi3.exec_command('pkill -f status.py')
    pi2.exec_command('pkill -f distort.py')
    pi2.exec_command('pkill -f sensor_board.py')
    pi3.exec_command('pkill -f ir.py')
    pi2.exec_command('pkill -f ir.py')
    ssh.exec_command('pkill -f keypad.py')
    ssh.exec_command('pkill -f read.py')

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
    #stdin = ssh.exec_command(command)[0]
    time.sleep(3)
    ssh.exec_command('python delete-locks.py')
    ssh.exec_command('python read.py')
    #ssh.exec_command('python keypad.py')
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
    #pi2.exec_command('python sensor_board.py')
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
    global ssh, pi2, pi3

    # Define the names and IP addresses of the Pis
    pi_names = {
        "top-pi": "192.168.0.104",
        "middle-pi": "192.168.0.105",
        "tree-pi": "192.168.0.114"
    }

    # Prepare a list of dictionaries containing Pi status data
    pi_statuses = []

    if ssh:
        pi1_status = {"name": "top-pi", "ip_address": pi_names["top-pi"]}
        try:
            if ssh.get_transport().is_active():
                pi1_status["ssh_active"] = "Online"
            else:
                pi1_status["ssh_active"] = "Offline"
        except AttributeError:
            pi1_status["ssh_active"] = "Offline"
        pi_statuses.append(pi1_status)

    if pi2:
        pi2_status = {"name": "middle-pi", "ip_address": pi_names["middle-pi"]}
        try:
            if pi2.get_transport().is_active():
                pi2_status["ssh_active"] = "Online"
            else:
                pi2_status["ssh_active"] = "Offline"
        except AttributeError:
            pi2_status["ssh_active"] = "Offline"
        pi_statuses.append(pi2_status)

    if pi3:
        pi3_status = {"name": "tree-pi", "ip_address": pi_names["tree-pi"]}
        try:
            if pi3.get_transport().is_active():
                pi3_status["ssh_active"] = "Online"
            else:
                pi3_status["ssh_active"] = "Offline"
        except AttributeError:
            pi3_status["ssh_active"] = "Offline"
        pi_statuses.append(pi3_status)

    # Render the template fragment and return as JSON
    return jsonify(render_template('status_table_fragment.html', pi_statuses=pi_statuses))
if romy == False:
    turn_on_api()
    start_scripts()
    #scheduler.add_job(start_bird_sounds, 'interval', minutes=1)

@app.route('/')
def index():
    return render_template('index.html')
if __name__ == '__main__':
    signal.signal(signal.SIGINT, handle_interrupt)
    app.run(host='0.0.0.0', port=80)
    if romy == False:
        atexit.register(cleanup)