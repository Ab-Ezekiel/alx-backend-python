#!/usr/bin/python3
import sys

lazy_paginator = __import__('2-lazy_paginate').lazy_pagination

try:
    for page in lazy_paginator(100):  # fetch 100 users per page
        for user in page:
            print(user)

except BrokenPipeError:
    sys.stderr.close()
