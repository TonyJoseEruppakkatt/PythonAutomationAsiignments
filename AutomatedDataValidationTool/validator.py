import re
import pandas as pd


# Check whether a value is empty
def is_empty(value):

    return pd.isna(value) or str(value).strip() == ""


# Validate email format
def validate_email(value):

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    return bool(re.match(pattern, str(value)))


# Validate phone number
def validate_phone(value):

    phone = str(value).strip()

    return bool(re.fullmatch(r"\d{10}", phone))


# Validate numeric values
def validate_numeric(value, rules):

    try:

        number = float(value)

    except (ValueError, TypeError):

        return False

    if "min" in rules and number < rules["min"]:
        return False

    if "max" in rules and number > rules["max"]:
        return False

    return True


# Validate individual records
def validate_records(df, rules):

    invalid_records = []
    valid_records = []

    seen_records = set()

    for index, row in df.iterrows():

        errors = []

        # Check duplicate records
        record_key = tuple(
            str(value).strip() for value in row.tolist()
        )

        if record_key in seen_records:

            errors.append("Duplicate record found")

        else:

            seen_records.add(record_key)

        # Check each column
        for column, rule in rules.items():

            if column not in df.columns:

                continue

            value = row[column]

            # Mandatory validation
            if rule.get("required", False) and is_empty(value):

                errors.append(f"{column}: Mandatory field is missing")

                continue

            if is_empty(value):

                continue

            # Email validation
            if rule.get("type") == "email":

                if not validate_email(value):

                    errors.append(f"{column}: Invalid email format")

            # Phone validation
            elif rule.get("type") == "phone":

                if not validate_phone(value):

                    errors.append(f"{column}: Invalid phone number")

            # Integer validation
            elif rule.get("type") == "integer":

                try:

                    number = float(value)

                    if not number.is_integer():

                        errors.append(f"{column}: Must be an integer")

                    elif not validate_numeric(number, rule):

                        errors.append(f"{column}: Value outside allowed range")

                except (ValueError, TypeError):

                    errors.append(f"{column}: Must be a valid integer")

            # Numeric validation
            elif rule.get("type") == "number":

                if not validate_numeric(value, rule):

                    errors.append(f"{column}: Invalid numeric value or range")

            # Allowed values validation
            if "allowed_values" in rule:

                allowed = rule["allowed_values"]

                if str(value).strip() not in allowed:

                    errors.append(f"{column}: Value not allowed")

        # Separate valid and invalid records
        record = row.to_dict()

        if errors:

            record["Validation Errors"] = "; ".join(errors)

            invalid_records.append(record)

        else:

            valid_records.append(record)

    return valid_records, invalid_records