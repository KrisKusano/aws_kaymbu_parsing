import logging
from datetime import datetime as dt
from typing import Any, Dict

import dash
import dash_core_components as dcc
import dash_html_components as html

from get_data import compute_nap_times
from test.test_get_data import get_test_week_data

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


def create_app(is_test: bool=False):
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    app.config['TESTING'] = is_test

    if is_test:
        start_date = dt(2018, 10, 1)
    else:
        start_date = dt.today()

    app.layout = html.Div(children=[
        html.H1(children="Emilia's Gretchen's House Activities"),
        dcc.DatePickerSingle(
            id='date-picker-week',
            date=start_date,
            min_date_allowed=dt(2018, 9, 1),
            max_date_allowed=dt.today(),
            initial_visible_month=dt.today()
        ),
        dcc.Graph(id='nap-time-bar-graph')
    ])

    @app.callback(
        dash.dependencies.Output('nap-time-bar-graph', 'figure'),
        [dash.dependencies.Input('date-picker-week', 'date')]
    )
    def update_nap_graph(date: str) -> Dict[str, Any]:
        """
        Plot sleep time
        """
        if app.config['TESTING']:
            data = get_test_week_data()
        else:
            raise NotImplementedError('No real data yet...')

        # parse out nap times
        naps = compute_nap_times(data['Items'])
        nap_start, nap_length_s = zip(*naps)

        # compute average, convert to minutes
        if nap_length_s:
            avg_length_s = sum(nap_length_s) / len(nap_length_s)
        else:
            avg_length_s = None

        nap_length_min = [x / 60 for x in nap_length_s]
        avg_length_min = avg_length_s / 60

        return {
            'data': [
                {'x': nap_start,
                 'y': nap_length_min,
                 'type': 'bar',
                 'name': 'naps'},
                {'x': [nap_start[0], nap_start[-1]],
                 'y': [avg_length_min] * 2,
                 'type': 'line',
                 'name': 'average'}
            ],
            'layout': {
                'title': 'Naps'
            }
        }

    return app

if __name__ == '__main__':
    logging.basicConfig(level='INFO')
    app = create_app(is_test=True)
    app.run_server(debug=True)
