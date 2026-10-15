# Edit these to match your MySQL login (or set them as environment variables).
import os
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")          # <- put your MySQL password here
DB_NAME = "legal_desk"
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-before-real-use")
