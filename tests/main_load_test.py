""" Module providing a function to send a message to the server. """

from client_load_test import send_message


async def run_client():
    """ Function to send a message to the server. """
    await send_message("16;0;21;11;0;19;4;0;")


async def main():
    """ Function to start the client. """
    await run_client()
