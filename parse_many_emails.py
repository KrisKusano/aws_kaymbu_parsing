import logging
import os
import sys

from note_parse import parse_gretchens_notes
from test import _load_email

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    input_dir = sys.argv[1]
    for file_path in os.listdir(input_dir):
        logging.info('Parsing {}'.format(file_path))
        full_path = os.path.join(input_dir, file_path)
        payload = _load_email(full_path)
        parse_gretchens_notes(payload)