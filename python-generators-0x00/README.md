# Python Generators — Getting started (seed + streaming)

This folder provides a simple `seed.py` script to create a MySQL database `ALX_prodev`, a `user_data` table,
populate it from `user_data.csv`, and a generator `stream_user_rows()` that yields rows one-by-one.

## Requirements

- Python 3.8+
- Install MySQL connector:
  ```bash
  pip install mysql-connector-python
