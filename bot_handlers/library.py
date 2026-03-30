import logging
import os
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)