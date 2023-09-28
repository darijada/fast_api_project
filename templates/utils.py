def format_currency(value):
    """
    Format a numerical value as a currency string.

    :param value: The numerical value to format as currency.
    :return: The formatted currency string.
    """
    formatted_value = (
        "{:,.2f}".format(value).replace(",", " ").replace(".", ",").replace(" ", ".")
    )
    return formatted_value
