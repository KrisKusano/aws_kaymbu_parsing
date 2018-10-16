from argparse import ArgumentParser
import logging
from dash_app.application import create_app

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--testing', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(level='INFO')
    app = create_app(is_test=args.testing)
    app.run_server(debug=True)
