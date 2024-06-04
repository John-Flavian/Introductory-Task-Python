# Algo-Science-Assessment

## Project Setup

This guide will walk you through setting up the Algo-Science-Assessment project.
Follow the steps below to create a virtual environment, install dependencies, start the server, run the client, perform unit tests, and conduct load tests.

### Step 1: Create a Virtual Environment
First, create a virtual environment to isolate your project dependencies.

```bash
python3 -m venv venv
```

### Step 2: Activate the Virtual Environment
Activate the virtual environment. The steps differ based on your operating system:

**On Windows:**
```bash
.\venv\Scripts\activate
```

**On macOS and Linux:**
```bash
source venv/bin/activate
```

### Step 3: Install Dependencies
With the virtual environment activated, install the required dependencies:

```bash
pip install -r requirements.txt
```

### Step 4: Start the Server
Start the server using the following command:

```bash
python3 src/server.py
```

### Step 5: Run the Client
In another terminal instance (with the virtual environment activated), run the client:

```bash
python3 src/client.py
```

### Step 6: Run Unit Tests for the Server
To run the unit tests for the server script and view the logs, execute:

```bash
PYTHONPATH=. pytest tests/server_unit_test.py -s
```

### Step 7: Run Load Tests for the Server
To conduct load tests, follow these steps:

1. **Start the Server:** Ensure the server is running.
   ```bash
   python3 src/server.py
   ```

2. **Open Another Terminal Instance:** With the virtual environment activated, run:
   ```bash
   locust -f tests/locust_load_test.py
   ```

3. **Open Locust Web Interface:** Visit [http://localhost:8089](http://localhost:8089) in your browser.

4. **Configure Load Test:** Enter the desired number of users and ramp-up rate per second, then click "Start".

By following these steps, you will set up the project environment, install dependencies, run the server and client, execute unit tests, and perform load testing efficiently.