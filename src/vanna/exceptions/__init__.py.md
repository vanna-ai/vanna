## Table of Contents 🔗

- [ImproperlyConfigured](#ImproperlyConfigured) 
- [DependencyError](#DependencyError)
- [ConnectionError](#ConnectionError) 
- [OTPCodeError](#OTPCodeError)
- [SQLRemoveError](#SQLRemoveError)
- [ExecutionError](#ExecutionError)
- [ValidationError](#ValidationError)
- [APIError](#APIError)


## <a name="ImproperlyConfigured"></a>ImproperlyConfigured 🛑

`ImproperlyConfigured` is raised when the configuration is incorrect.

**Example usage:**

```python
if not settings.REQUIRED_SETTING:
    raise ImproperlyConfigured("REQUIRED_SETTING is not set")
```

## <a name="DependencyError"></a>DependencyError 🧩

`DependencyError` is raised when a required dependency is missing.

**Example usage:**

```python
try:
    import missing_dependency
except ImportError:
    raise DependencyError("missing_dependency is not installed")
```

## <a name="ConnectionError"></a>ConnectionError 🔌

`ConnectionError` is raised when unable to establish a connection.

**Example usage:**

```python
try:
    client.connect()
except ConnectionError:
    print("Unable to connect to the database.")
```

## <a name="OTPCodeError"></a>OTPCodeError 🔑

`OTPCodeError` is raised when the OTP code is invalid or cannot be sent.

**Example usage:**

```python
try:
    send_otp(user.phone_number)
except OTPCodeError:
    print("Invalid or expired OTP code.")
```

## <a name="SQLRemoveError"></a>SQLRemoveError 🗑️

`SQLRemoveError` is raised when unable to remove SQL.

**Example usage:**

```python
try:
    delete_user(user.id)
except SQLRemoveError:
    print("Unable to remove user from the database.")
```

## <a name="ExecutionError"></a>ExecutionError 🚫

`ExecutionError` is raised when unable to execute code.

**Example usage:**

```python
try:
    execute_query("SELECT * FROM users")
except ExecutionError:
    print("Unable to execute query.")
```

## <a name="ValidationError"></a>ValidationError ⚠️

`ValidationError` is raised for validation errors.

**Example usage:**

```python
try:
    validate_form(request.POST)
except ValidationError as e:
    print(e.messages)
```

## <a name="APIError"></a>APIError 🌐

`APIError` is raised for API errors.

**Example usage:**

```python
try:
    response = api_client.get("/users")
except APIError as e:
    print(e.status_code, e.message)
```