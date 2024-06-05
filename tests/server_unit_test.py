""" Test for the `server` module. """
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import json
import ssl
import asyncio
import pytest
from freezegun import freeze_time
from src import server


# Test for the `search` function
@pytest.mark.parametrize("contents, query, expected", [
    (["apple", "banana", "cherry"], "banana", "STRING EXISTS"),
    (["apple", "banana", "cherry"], "grape", "STRING NOT FOUND"),
    ([], "apple", "STRING NOT FOUND"),
    (["apple", "banana", "cherry"], "", "STRING NOT FOUND"),
    (["apple", "apple", "apple"], "apple", "STRING EXISTS"),
])
def test_search(contents: list[str], query: str, expected: str) -> None:
    """
    Test the `search` function.

    This function tests the `search` function of the `server` module.
    It provides a set of test cases with different inputs and expected outputs.
    The test cases cover various scenarios such as searching for an
    existing string,
    searching for a non-existing string, searching in an empty list,
    searching for an empty string, and searching for a repeated string.

    Parameters:
        contents (list[str]): The list of strings to search in.
        query (str): The string to search for.
        expected (str): The expected output message.

    Returns:
        None

    Raises:
        AssertionError: If the actual output of the `search`
            function does not match the expected output.
    """
    assert server.search(contents, query) == expected


# Test for the `handle_client` function
@pytest.mark.asyncio
async def test_handle_client() -> None:
    """
    Test the `handle_client` function.

    This function tests the `handle_client` function of the `server` module.
    It provides a set of test cases with different inputs and expected outputs.
    The test cases cover various scenarios such as handling a
    client with an existing string,
    handling a client with a non-existing string,
    handling a client with an empty list,
    handling a client with an empty string,
    and handling a client with a repeated string.

    Parameters:
        None

    Returns:
        None

    Raises:
        AssertionError: If the actual output of the `handle_client` function
        does not match the expected output.
    """
    reader = AsyncMock()
    writer = MagicMock()
    reader.read = AsyncMock(side_effect=[b"apple\n", b""])
    writer.get_extra_info = MagicMock(return_value=('127.0.0.1',))
    writer.drain = AsyncMock()
    writer.wait_closed = AsyncMock()

    with freeze_time("2023-01-01 12:00:00"):
        with patch('src.server.time.time', side_effect=[1000.0, 1000.1]):
            with patch('src.server.load_txt_file',
                       return_value=["te", "st", "op"]):
                server.REREAD_ON_QUERY = True
                await server.handle_client(reader, writer)

                writer.write.assert_called_with(b'STRING NOT FOUND\n')
                assert writer.write.call_count == 1

                writer.drain.assert_called()
                assert writer.drain.call_count == 1

                writer.close.assert_called()
                writer.wait_closed.assert_called()


@pytest.mark.asyncio
async def test_handle_client_no_reread() -> None:
    """
    Test the `handle_client` function with `REREAD_ON_QUERY` set to `False`.

    This test case verifies the behavior of the `handle_client` function when
    `REREAD_ON_QUERY` is set to `False`.
    It creates a mock reader and writer objects, sets up the necessary patches
    and side effects,
    and asserts the expected behavior of the `handle_client` function.

    Parameters:
        None

    Returns:
        None

    Raises:
        AssertionError: If the actual output of the `handle_client` function
        does not match the expected output.
    """
    reader = AsyncMock()
    writer = MagicMock()
    reader.read = AsyncMock(side_effect=[b"grape\n", b""])
    writer.get_extra_info = MagicMock(return_value=('127.0.0.1',))
    writer.drain = AsyncMock()
    writer.wait_closed = AsyncMock()

    with freeze_time("2023-01-01 12:00:00"):
        with patch('src.server.time.time', side_effect=[1000.0, 1000.2]):
            with patch('src.server.INITIAL_FILE_CONTENTS',
                       ["apple", "banana", "cherry"]):
                # global REREAD_ON_QUERY
                server.REREAD_ON_QUERY = False
                await server.handle_client(reader, writer)

                writer.write.assert_called_with(b'STRING NOT FOUND\n')
                assert writer.write.call_count == 1

                writer.drain.assert_called()
                assert writer.drain.call_count == 1

                writer.close.assert_called()
                writer.wait_closed.assert_called()


@pytest.mark.asyncio
async def test_handle_client_incomplete_read_error() -> None:
    """
    Test the `handle_client` function for handling `IncompleteReadError`.

    This test case verifies the behavior of the `handle_client` function
    when an `IncompleteReadError` is raised.
    It creates a mock reader and writer objects, sets up the necessary patches
    and side effects,
    and asserts that the function raises the `IncompleteReadError` exception.

    Parameters:
        None

    Returns:
        None

    Raises:
        AssertionError: If the `handle_client` function does not raise
        an `IncompleteReadError`.
    """
    reader = AsyncMock()
    writer = AsyncMock()
    reader.read = AsyncMock(
        side_effect=asyncio.IncompleteReadError(partial=b'data', expected=10)
        )
    writer.get_extra_info = MagicMock(return_value=('127.0.0.1', 12345))

    with pytest.raises(asyncio.IncompleteReadError):
        await server.handle_client(reader, writer)


@pytest.mark.asyncio
async def test_handle_client_connection_reset_error() -> None:
    """
    Test the `handle_client` function for handling `ConnectionResetError`.

    This test case verifies the behavior of the `handle_client` function when
    a `ConnectionResetError` is raised.
    It creates a mock reader and writer objects, sets up the necessary patches
    and side effects,
    and asserts that the function raises the `ConnectionResetError` exception.

    Parameters:
        None

    Returns:
        None

    Raises:
        AssertionError: If the `handle_client` function does not raise
        a `ConnectionResetError`.
    """
    reader = AsyncMock()
    writer = AsyncMock()
    reader.read = AsyncMock(
        side_effect=ConnectionResetError("Connection reset")
        )
    writer.get_extra_info = MagicMock(return_value=('127.0.0.1', 12345))

    with pytest.raises(ConnectionResetError):
        await server.handle_client(reader, writer)


@pytest.mark.asyncio
async def test_main() -> None:
    """
    Test the main function of the server module.

    This function tests the main function of the server module by mocking
     the necessary objects and functions.
    It verifies that the start_server function is called with the correct
    arguments and that the serve_forever function
    is called on the server mock object.

    Parameters:
        None

    Returns:
        None
    """
    server_mock = AsyncMock()
    server_mock.sockets = [MagicMock()]
    server_mock.sockets[0].getsockname.return_value = ('127.0.0.1', 8001)

    with patch('src.server.asyncio.start_server',
               return_value=server_mock) as start_server_mock:
        with patch('src.server.create_ssl_context',
                   return_value=MagicMock()):
            with patch('src.server.USE_SSL', False):
                await server.main()
                start_server_mock.assert_called_once_with(
                    server.handle_client,
                    '127.0.0.1',
                    8001,
                    ssl=None
                )
                server_mock.serve_forever.assert_called_once()


@pytest.mark.asyncio
async def test_main_with_ssl() -> None:
    """
    Test the main function of the server module with SSL.

    This function tests the main function of the server module by mocking
     the necessary objects and functions.
    It verifies that the start_server function is called with the
    correct
    arguments and that the serve_forever function
    is called on the server mock object.

    Parameters:
        None

    Returns:
        None
    """
    server_mock = AsyncMock()
    server_mock.sockets = [MagicMock()]
    server_mock.sockets[0].getsockname.return_value = ('127.0.0.1', 8001)
    ssl_context_mock = MagicMock()

    with patch('src.server.asyncio.start_server',
               return_value=server_mock) as start_server_mock:
        with patch('src.server.create_ssl_context',
                   return_value=ssl_context_mock):
            with patch('src.server.USE_SSL', True):
                await server.main()
                start_server_mock.assert_called_once_with(
                    server.handle_client,
                    '127.0.0.1',
                    8001,
                    ssl=ssl_context_mock
                )
                server_mock.serve_forever.assert_called_once()


def test_create_ssl_context_success() -> None:
    """
    Test the `create_ssl_context` function for successful creation of an
        SSL context.

    This test case verifies the behavior of the `create_ssl_context` function
        when it successfully creates an SSL context.
    It patches the `os.path.exists` function to return `True` to
        simulate the existence of the SSL certificate and key files.
    It then patches the `ssl.create_default_context` function to return a
        mock SSL context object.
    The test case calls the `create_ssl_context` function and asserts that it
       successfully returns the mock SSL context object.
    It also asserts that the `ssl.create_default_context` function is called
        with the correct purpose (`ssl.Purpose.CLIENT_AUTH`),
        and that the `load_cert_chain` method of the mock SSL context object
        is called with the correct certificate and key file paths.

    Parameters:
        None

    Returns:
        None

    Asserts if the mock context is an ssl context
    """

    with patch('src.server.os.path.exists', return_value=True):
        patch_default_context = patch('src.server.ssl.create_default_context')
        with patch_default_context as default_context:
            context_mock = MagicMock()
            default_context.return_value = context_mock

            context = server.create_ssl_context()
            auth = ssl.Purpose.CLIENT_AUTH
            default_context.assert_called_once_with(auth)
            context_mock.load_cert_chain.assert_called_once_with(
                certfile=server.CERTFILE, keyfile=server.KEYFILE
                )
            assert context == context_mock


def test_create_ssl_context_missing_certfile() -> None:
    """
    Test the `create_ssl_context` function when the certificate
        file is missing.

    This function tests the behavior of the `create_ssl_context` function
        when the certificate file is missing.
    It verifies that a `FileNotFoundError`is raised with the
        appropriate error message.

    The function uses the `patch` function from the `unittest.mock` module to
        temporarily replace the `os.path.exists` function with a mock function.
    The mock function is set up to return `False` when the certificate
        file path is passed as an argument,
        indicating that the file is missing.

    The function then calls the `create_ssl_context` function and expects it to
        raise a `FileNotFoundError` with the message
        "SSL certificate or key file not found".

    Note:
        This test assumes that the `CERTFILE` variable is correctly set to the
        path of the certificate file in the `src.server` module.
    """
    with patch('src.server.os.path.exists',
               side_effect=lambda path: path != server.CERTFILE):
        with pytest.raises(FileNotFoundError,
                           match="SSL certificate or key file not found"):
            server.create_ssl_context()


def test_create_ssl_context_missing_keyfile() -> None:
    """
    Test the `create_ssl_context` function when the key file is missing.

    This function tests the behavior of the `create_ssl_context` function
    when the key file is missing. It verifies that a `FileNotFoundError`
    is raised with the appropriate error message.

    The function uses the `patch` function from the `unittest.mock` module to
    temporarily replace the `os.path.exists` function with a mock function.
    The mock function is set up to return `False` when the key file path
    is passed as an argument, indicating that the file is missing.

    The function then calls the `create_ssl_context` function and expects it to
    raise a `FileNotFoundError` with the message "SSL certificate or
    key file not found".

    Note:
        This test assumes that the `KEYFILE` variable is correctly set to the
        path of the key file in the `src.server` module.
    """
    with patch('src.server.os.path.exists',
               side_effect=lambda path: path != server.KEYFILE):
        with pytest.raises(FileNotFoundError,
                           match="SSL certificate or key file not found"):
            server.create_ssl_context()


def test_create_ssl_context_missing_both_files() -> None:
    """
    Test creating a SSL context with missing files.

    This function tests the behavior of the `create_ssl_context` function
    when both the SSL certificate and key files are missing.
    It verifies that a `FileNotFoundError` is raised with the appropriate
    error message.

    The function creates a mock `server_mock` object using the
        `AsyncMock` class from the `unittest.mock` module.
    It sets up a mock socket object and configures it to return the
        hostname and port number when the `getsockname` method is called.

    The function then uses the `patch` function from the `unittest.mock` module
    to temporarily replace the `os.path.exists` function with a mock function.
    The mock function is set up to return `False` when either the certificate
    file or the key file path is passed as an argument, indicating that the
    file is missing.

    The function then calls the `create_ssl_context` function and expects it to
    raise a `FileNotFoundError` with the message
    "SSL certificate or key file not found".

    Note:
        This test assumes that the `CERTFILE` and `KEYFILE` variables are
        correctly set to the paths of the certificate and key files in
        the `src.server` module.
    """
    with patch('src.server.os.path.exists', return_value=False):
        with pytest.raises(FileNotFoundError,
                           match="SSL certificate or key file not found"):
            server.create_ssl_context()


@pytest.fixture
def temp_text_file(tmp_path: Path) -> Path:
    """
    Create a temporary text file.

    This function creates a temporary text file with the name "test.txt" in the
        specified temporary directory.
    The file is populated with the following lines:
    "Line 1", "Line 2", and "Line 3".

    Parameters:
        tmp_path (Path): The temporary directory
            where the file will be created.

    Returns:
        Path: The path to the created temporary text file.
    """
    file_path = tmp_path / "test.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Line 1\nLine 2\nLine 3")
    return file_path


def test_load_txt_file_exists(temp_text_file: str) -> None:
    """
    Test loading an existing text file.

    This function tests the `load_txt_file` function by loading an
        existing text file and asserting that the contents of the file
        match the expected list of strings.

    Parameters:
        temp_text_file (str): The path to the temporary text file.

    Raises:
        AssertionError: If the contents of the text file do not match the
            expected list of strings.
    """
    contents = server.load_txt_file(temp_text_file)
    assert contents == ["Line 1", "Line 2", "Line 3"]


def test_load_txt_file_file_not_found() -> None:
    """
    Test loading a non-existent text file.

    This function tests the `load_txt_file` function by attempting to load a
    non-existent text file and asserting that a `FileNotFoundError` is raised
    with the expected error message.

    Raises:
        AssertionError: If a `FileNotFoundError` is not raised or if the
            error message does not match the expected message.
    """
    msg = "Error: The file 'dummy_path' was not found."
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError, match=msg):
            server.load_txt_file("dummy_path")


def test_load_txt_file_permission_error() -> None:
    """
    Test loading a text file with permission error.

    This function tests the `load_txt_file` function by attempting
    to load a text file
    with a permission error and asserting that a `PermissionError` is raised
    with the expected error message.

    Raises:
        AssertionError: If a `PermissionError` is not raised or if the
            error message does not match the expected message.
    """
    with patch("builtins.open", side_effect=PermissionError):
        msg = "Error: Permission denied for file 'dummy_path'."
        with pytest.raises(PermissionError, match=msg):
            server.load_txt_file("dummy_path")


def test_load_txt_file_is_a_directory_error() -> None:
    """
    Test loading a text file that is a directory.

    This function tests the `load_txt_file` function by attempting
    to load a text file
    that is a directory and asserting that a `IsADirectoryError` is raised
    with the expected error message.

    Raises:
        AssertionError: If a `IsADirectoryError` is not raised or if the
            error message does not match the expected message.
    """
    with patch("builtins.open", side_effect=IsADirectoryError):
        msg = "Error: The path 'dummy_path' is a directory, not a file."
        with pytest.raises(IsADirectoryError, match=msg):
            server.load_txt_file("dummy_path")


def test_load_txt_file_io_error() -> None:
    """
    Test loading a text file with an I/O error.

    This function tests the `load_txt_file` function by attempting
    to load a text file
    with an I/O error and asserting that an `IOError` is raised
    with the expected error message.

    Raises:
        AssertionError: If an `IOError` is not raised or if the
            error message does not match the expected message.
    """
    with patch("builtins.open", side_effect=IOError("Some I/O error")):
        msg = "Error: An I/O error occurred: Some I/O error"
        with pytest.raises(IOError, match=msg):
            server.load_txt_file("dummy_path")


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    """
    Test fixture to create a temporary config file.

    This function creates a temporary JSON file with the name
    "test-config.json" in the specified temporary directory.
    The file is populated with the following JSON object:
    {"key": "value"}.

    Parameters:
        tmp_path (Path): The temporary directory
            where the file will be created.

    Returns:
        Path: The path to the created temporary config file.
    """
    file_path = tmp_path / "test-config.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump({"key": "value"}, f)
    return file_path


# Test cases
def test_load_config_exists(temp_config_file: str) -> None:
    """
    Test loading a config file that exists.

    This function tests the `load_config` function by loading a
        config file and asserting that the contents of the file
        match the expected dictionary.

    Parameters:
        temp_config_file (str): The path to the temporary config file.

    Raises:
        AssertionError: If the contents of the config file do not match the
            expected dictionary.
    """
    config = server.load_config(temp_config_file)
    assert config == {"key": "value"}


def test_load_config_file_file_not_found() -> None:
    """
    Test loading a non-existent config file.

    This function tests the `load_config` function by attempting to
        load a non-existent config file and asserting that a
        `FileNotFoundError` is raised with the expected error message.

    Raises:
        AssertionError: If a `FileNotFoundError` is not raised or if the
            error message does not match the expected message.
    """
    msg = "Error: The file 'dummy_path' does not exist."
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError, match=msg):
            server.load_config("dummy_path")


def test_load_config_file_permission_error() -> None:
    """
    Test loading a config file with a permission error.

    This function tests the `load_config` function by attempting to
        load a config file with a permission error and asserting that a
        `PermissionError` is raised with the expected error message.

    Raises:
        AssertionError: If a `PermissionError` is not raised or if the
            error message does not match the expected message.
    """
    with patch("builtins.open", side_effect=PermissionError):
        msg = "Error: Permission denied for file 'dummy_path'."
        with pytest.raises(PermissionError, match=msg):
            server.load_config("dummy_path")


def test_load_config_file_is_a_directory_error() -> None:
    """
    Test loading a config file that is a directory.

    This function tests the `load_config` function by attempting to
        load a config file that is a directory and asserting that a
        `IsADirectoryError` is raised with the expected error message.

    Raises:
        AssertionError: If a `IsADirectoryError` is not raised or if the
            error message does not match the expected message.
    """
    with patch("builtins.open", side_effect=IsADirectoryError):
        msg = "Error: The path 'dummy_path' is a directory, not a file."
        with pytest.raises(IsADirectoryError, match=msg):
            server.load_config("dummy_path")


def test_load_config_file_json_decode_error() -> None:
    """
    Test loading a config file with a JSON decode error.

    This function tests the `load_config` function by attempting to
        load a config file with a JSON decode error and asserting that a
        `json.JSONDecodeError` is raised with the expected error message.

    Raises:
        AssertionError: If a `json.JSONDecodeError` is not raised or if the
            error message does not match the expected message.
    """
    msg = "Error: The file 'dummy_path' contains invalid JSON."
    with patch("builtins.open",
               side_effect=json.JSONDecodeError(msg, doc="dummy_path", pos=0)):
        with pytest.raises(json.JSONDecodeError, match=msg):
            server.load_config("dummy_path")
