import phonenumbers

def format_phone(phone_number: str, country: str) -> str:
    try:
        parsed = phonenumbers.parse(phone_number, country)

        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid phone number")

        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        raise ValueError("Invalid phone number format")