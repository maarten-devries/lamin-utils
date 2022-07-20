from lamin_logger import colors, logger


def test_logger():
    assert logger.level("INFO").name == "INFO"
    assert colors.green("text") == "\x1b[1;92mtest\x1b[0m"
