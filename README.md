# Algo-Science-Assessment

## Project Setup

### Create a virtual environment
python3 -m venv venv

### Activate the virtual environment
On Windows:

bash
.\venv\Scripts\activate

On macOS and Linux:
bash

source venv/bin/activate

## Install dependencies
pip install -r requirements.txt


## Start the server
python3 src/server.py

## Run the client
python3 src/client.py


## Testing

### Run the unit tests for the server script and view the logs
PYTHONPATH=. pytest tests/server_unit_test.py -s

### Run the unit tests for the server script and without logs
PYTHONPATH=. pytest tests/server_unit_test.py


### Run load tests for the server
Start the server:
python3 src/server.py

Open another instance of the terminal and run:
locust -f tests/locust_load_test.py 
Then visit: http://localhost:8089

Enter the number of Users and ramp up per second
then click start.
