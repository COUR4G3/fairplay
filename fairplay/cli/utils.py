import shutil


def format_header(names, widths, separator=" | "):
    header = format_line(names, widths, separator)
    header += "\n"

    border = []
    for _name, width in zip(names, widths):
        if width == -1:
            maxwidth, _ = shutil.get_terminal_size()
            width = maxwidth - sum(widths) - (len(separator) * len(widths))
        border.append("-" * width)

    header += format_line(border, widths, separator)
    return header


def format_line(values, widths, separator=" | "):
    line = []
    for value, width in zip(values, widths):
        value = str(value)

        if width == -1:
            maxwidth, _ = shutil.get_terminal_size()
            width = maxwidth - sum(widths) - (len(separator) * len(widths))

        line.append(value.ljust(width))
    return separator.join(line)
