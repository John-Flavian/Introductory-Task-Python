""" Test for the `server` module. """
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import json
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
    """ Test for the `search` function. """
    assert server.search(contents, query) == expected


# Test for the `handle_client` function
@pytest.mark.asyncio
async def test_handle_client() -> None:
    """ Test for the `handle_client` function. """
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
    """ Test for the `handle_client` function `with
    REREAD_ON_QUERY = False`. """
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
    server_mock.sockets[0].getsockname.return_value = ('localhost', 8080)

    with patch('src.server.asyncio.start_server',
               return_value=server_mock) as start_server_mock:
        with patch('src.server.create_ssl_context',
                   return_value=MagicMock()):
            with patch('src.server.USE_SSL', False):
                await server.main()
                start_server_mock.assert_called_once_with(
                    server.handle_client,
                    'localhost',
                    8080,
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
    server_mock.sockets[0].getsockname.return_value = ('localhost', 8080)
    ssl_context_mock = MagicMock()

    with patch('src.server.asyncio.start_server',
               return_value=server_mock) as start_server_mock:
        with patch('src.server.create_ssl_context',
                   return_value=ssl_context_mock):
            with patch('src.server.USE_SSL', True):
                await server.main()
                start_server_mock.assert_called_once_with(
                    server.handle_client,
                    'localhost',
                    8080,
                    ssl=ssl_context_mock
                )
                server_mock.serve_forever.assert_called_once()


def test_create_ssl_context_success() -> None:
    """ Test creating a SSL context. """
    # certfile = "certs/certificate.pem"
    # keyfile = "certs/key.pem"

    with patch('src.server.os.path.exists', return_value=True):
        patch_default_context = patch('src.server.ssl.create_default_context')
        with patch_default_context as default_context:
            context_mock = MagicMock()
            default_context.return_value = context_mock

            context = server.create_ssl_context()
            auth = server.ssl.Purpose.CLIENT_AUTH
            default_context.assert_called_once_with(auth)
            context_mock.load_cert_chain.assert_called_once_with(
                certfile=server.CERTFILE, keyfile=server.KEYFILE
                )
            assert context == context_mock


def test_create_ssl_context_missing_certfile() -> None:
    """ Test creating a SSL context with missing files. """
    with patch('src.server.os.path.exists',
               side_effect=lambda path: path != server.CERTFILE):
        with pytest.raises(FileNotFoundError,
                           match="SSL certificate or key file not found"):
            server.create_ssl_context()


def test_create_ssl_context_missing_keyfile() -> None:
    """ Test creating a SSL context with missing files. """
    with patch('src.server.os.path.exists',
               side_effect=lambda path: path != server.KEYFILE):
        with pytest.raises(FileNotFoundError,
                           match="SSL certificate or key file not found"):
            server.create_ssl_context()


def test_create_ssl_context_missing_both_files() -> None:
    """ Test creating a SSL context with missing files. """
    with patch('src.server.os.path.exists', return_value=False):
        with pytest.raises(FileNotFoundError,
                           match="SSL certificate or key file not found"):
            server.create_ssl_context()


@pytest.fixture
def temp_text_file(tmp_path: Path) -> Path:
    """Create a temporary text file."""
    file_path = tmp_path / "test.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Line 1\nLine 2\nLine 3")
    return file_path


def test_load_txt_file_exists(temp_text_file) -> None:
    """Test loading an existing text file."""
    contents = server.load_txt_file(temp_text_file)
    assert contents == ["Line 1", "Line 2", "Line 3"]


def test_load_txt_file_file_not_found():
    """ Test loading a text file that does not exist. """
    msg = "Error: The file 'dummy_path' was not found."
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError, match=msg):
            server.load_txt_file("dummy_path")


def test_load_txt_file_permission_error():
    """ Test loading a text file with a permission error. """
    with patch("builtins.open", side_effect=PermissionError):
        msg = "Error: Permission denied for file 'dummy_path'."
        with pytest.raises(PermissionError, match=msg):
            server.load_txt_file("dummy_path")


def test_load_txt_file_is_a_directory_error():
    """ Test loading a text file that is a directory. """
    with patch("builtins.open", side_effect=IsADirectoryError):
        msg = "Error: The path 'dummy_path' is a directory, not a file."
        with pytest.raises(IsADirectoryError, match=msg):
            server.load_txt_file("dummy_path")


def test_load_txt_file_io_error():
    """ Test loading a text file with an I/O error. """
    with patch("builtins.open", side_effect=IOError("Some I/O error")):
        msg = "Error: An I/O error occurred: Some I/O error"
        with pytest.raises(IOError, match=msg):
            server.load_txt_file("dummy_path")


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    """Create a temporary json file."""
    file_path = tmp_path / "test-config.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump({"key": "value"}, f)
    return file_path


# Test cases
def test_load_config_exists(temp_config_file) -> None:
    """Test loading an existing config file."""
    config = server.load_config(temp_config_file)
    assert config == {"key": "value"}


def test_load_config_file_file_not_found():
    """ Test loading a config file that does not exist. """
    msg = "Error: The file 'dummy_path' does not exist."
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError, match=msg):
            server.load_config("dummy_path")


def test_load_config_file_permission_error():
    """ Test loading a confic file with a permission error. """
    with patch("builtins.open", side_effect=PermissionError):
        msg = "Error: Permission denied for file 'dummy_path'."
        with pytest.raises(PermissionError, match=msg):
            server.load_config("dummy_path")


def test_load_config_file_is_a_directory_error():
    """ Test loading a config file that is a directory. """
    with patch("builtins.open", side_effect=IsADirectoryError):
        msg = "Error: The path 'dummy_path' is a directory, not a file."
        with pytest.raises(IsADirectoryError, match=msg):
            server.load_config("dummy_path")


def test_load_config_file_json_decode_error():
    """ Test loading a config file with an invalid JSON. """
    msg = "Error: The file 'dummy_path' contains invalid JSON."
    with patch("builtins.open",
               side_effect=json.JSONDecodeError(msg, doc="dummy_path", pos=0)):
        with pytest.raises(json.JSONDecodeError, match=msg):
            server.load_config("dummy_path")
