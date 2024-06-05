# Algorithmic Sciences Introductory Task

## Project Setup

Follow these steps to set up and run the Algorithmic-Sciences-Introductory-Task Project.

### Step 1: Create and Activate a Virtual Environment

**Create a virtual environment:**
```bash
python3 -m venv venv
```

**Activate the virtual environment:**

**On Windows:**
```bash
.\venv\Scripts\activate
```

**On macOS and Linux:**
```bash
source venv/bin/activate
```

### Step 2: Install Dependencies
Install the required dependencies:
```bash
pip install -r requirements.txt
```

### Step 3: Start the Server
Run the server:
```bash
python3 src/server.py
```

### Step 4: Configure the Client
Update the configuration options in `config/config.json`:

- `use_ssl`: Boolean, defaults to `false`. Activates SSL for both the server and the client.
- `certificate_file`: Path to `certificate.pem` file.
- `key_file`: Path to `key.pem` file. (The passphrase for the current key file is 'john')
- `txt_file`: Path to the `.txt` file to be searched.
- `reread_on_query`: Boolean, defaults to `false`.
- `server_host`: Server host.
- `server_port`: Server port.
- `client_host`: Server host.
- `client_port`: Server port.
- `prompt`: Boolean, defaults to `false`. If `true`, prompts the user to type in a search string.
- `query`: Query string for the client script, default is `"hi"`.

### Step 5: Run the Client
In another terminal instance (with the virtual environment activated), run the client:
```bash
python3 src/client.py
```

### Step 6: Run Unit Tests for the Server
Execute unit tests for the server script:
```bash
PYTHONPATH=. pytest tests/server_unit_test.py -s
```

### Step 7: Run Load Tests for the Server
1. **Ensure the server is running:**
   ```bash
   python3 src/server.py
   ```

2. **Open another terminal instance and run Locust:**
   ```bash
   locust -f tests/locust_load_test.py
   ```

3. **Open the Locust web interface:** Visit [http://localhost:8089](http://localhost:8089).

4. **Configure and start the load test:** Enter the number of users and ramp-up rate per second, then click "Start".

By following these steps, you will set up the project environment, install dependencies, run the server and client, execute unit tests, and perform load testing efficiently.

## Running the Server as a Linux Daemon

To run the server as a Linux daemon or service, follow these steps:

1. **Ensure you're logged in as the root user:**
   ```bash
   sudo -s
   ```

2. **Navigate to the systemd directory:**
   ```bash
   cd /etc/systemd/system
   ```

3. **Create a service file:**
   ```bash
   nano python-server.service
   ```

4. **Add the following content to the service file:**
   ```ini
   [Unit]
   Description=A script for running the server as a daemon.
   After=syslog.target network.target

   [Service]
   WorkingDirectory=/path_to_the_repo
   ExecStart=/path_to_the_repo/venv/bin/python src/server.py
   Restart=always
   RestartSec=120

   [Install]
   WantedBy=multi-user.target
   ```

5. **Save and exit the editor.**

6. **Reload the systemd daemon to apply changes:**
   ```bash
   systemctl daemon-reload
   ```

7. **Start the service:**
   ```bash
   systemctl start python-server
   ```

8. **Check the status of the service:**
   ```bash
   systemctl status python-server
   ```

By following these instructions, you can efficiently set up the project and ensure the server runs continuously as a background service.