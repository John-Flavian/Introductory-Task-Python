""" Module providing a Locust load test. """
import asyncio
import time
from locust import User, task, between, events
from main_load_test import main


class LoadTestUser(User):
    """ Locust user class. """
    wait_time = between(1, 2)

    @task
    def run_client(self):
        """ Function to send a message to the server. """
        start_time = time.time()
        try:

            asyncio.run(main())

            # Report success
            total_time = int((time.time() - start_time) * 1000)
            response_length = 0  # Adjust based on your actual response length
            events.request.fire(
                request_type="grpc", name="run_client",
                response_time=total_time, response_length=response_length,
                response=None, context=None, exception=None,
                start_time=start_time, url=None
            )
        except Exception as e:
            # Report failure
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="grpc", name="run_client",
                response_time=total_time, response_length=0,
                response=None, context=None, exception=e,
                start_time=start_time, url=None
            )


# Setup and teardown events
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """ Function to start the load test. """
    print("Starting load test...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """ Function to stop the load test. """
    print("Load test finished.")


@events.request.add_listener
def my_request_handler(request_type, name, response_time,
                       response_length, response,
                       context, exception, start_time, url, **kwargs):
    """ Function to handle the request. """
    if exception:
        print(f"Request to {name} failed with exception {exception}")
    else:
        print(f"Successfully made a request to: {name}")
        print("Response time:" + f"{response_time}"
              + " ms" + "\nResponse length: "
              + f"{response_length}"
              + " Response: " + f"{response}"
              + " Context: " + f"{context}"
              + " Exception: " + f"{exception}"
              + " Start time: " + f"{start_time} ms"
              + " URL: " + f"{url}"
              + f"\n {request_type}"
              )
