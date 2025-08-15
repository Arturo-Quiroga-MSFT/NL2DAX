import requests

def format_and_validate_dax(dax_code):
    url = "https://www.daxformatter.com/api/daxformatter/"
    payload = {
        "Dax": dax_code,
        "Separator": ",",
        "Annotations": False,
        "ShortenNames": False,
        "AddLineBreaks": True,
        "IncludeErrors": True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200 and response.text.strip():
            try:
                result = response.json()
                formatted_dax = result.get("FormattedDax", "")
                errors = result.get("Errors", [])
                if not formatted_dax and not errors:
                    return dax_code, ["DAX Formatter API returned no formatted DAX and no errors."]
                return formatted_dax, errors
            except Exception as e:
                return dax_code, [f"DAX Formatter API returned invalid JSON: {e}"]
        else:
            return dax_code, [f"DAX Formatter API error: HTTP {response.status_code} - {response.text.strip()}"]
    except Exception as e:
        return dax_code, [f"Exception during DAX Formatter API call: {e}"]

# Example usage:
if __name__ == "__main__":
    dax = "SUM('Table'[Column])"
    formatted, errors = format_and_validate_dax(dax)
    print("Formatted DAX:", formatted)
    if errors:
        print("Errors:", errors)
    else:
        print("No syntax errors detected.")
