from soil.logging import LogLevel, PrintLogger


def test_print_logger_formats_multiple_arguments():
    logger = PrintLogger()
    # Must not raise: two placeholders, two positional arguments
    logger.log(LogLevel.ERROR, "Type mismatch: '{}' does not fit type {}", "bogus", "STRING")