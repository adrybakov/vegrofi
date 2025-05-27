import os

import pytest

from vegrofi.__main__ import FileIsNotValid, check_file

directory = "file-examples/not-valid"
files = [os.path.join(directory, filename) for filename in os.listdir(directory)]


@pytest.mark.parametrize("filename", files)
def test_all(filename):
    error_messages = check_file(filename)

    assert len(error_messages) != 0
