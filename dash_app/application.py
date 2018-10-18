from datetime import datetime as dt
from datetime import timedelta
from typing import Any, Dict

import dash
import dash_core_components as dcc
import dash_html_components as html
from flask_caching import Cache

from .get_data import compute_nap_times, get_activty_table, get_week_data
from .test.test_get_data import get_test_week_data

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

DATE_FMT = "%Y-%m-%d"


def compute_week_start(date):
    day = dt.strptime(date, DATE_FMT)
    start_week = day - timedelta(days=day.weekday())
    return start_week.strftime(DATE_FMT)


def create_app(is_test: bool=False):
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    app.title = 'Daycare Activity Log'
    app.config['TESTING'] = is_test
    # required if callbacks are in a different file
    # app.config.suppress_callback_exceptions = True

    # set up a cache for memory.
    # Simple is in memory pickle, redis is suggested for higher performance...
    cache_config = {
        'CACHE_TYPE': 'simple'
    }
    cache = Cache()
    cache.init_app(app.server, config=cache_config)

    if is_test:
        start_date = dt(2018, 10, 1)
    else:
        start_date = dt.today().strftime(DATE_FMT)

    app.layout = html.Div(children=[
        html.H1(children="Emilia's Gretchen's House Activities"),
        html.H2(children="Naps"),
        html.Div([
            html.Div(children="Week Date:",
                     className="two columns"),
            html.Div([
                dcc.DatePickerSingle(
                    id='date-picker-week',
                    date=start_date,
                    min_date_allowed=dt(2018, 9, 1),
                    max_date_allowed=dt.today(),
                    initial_visible_month=start_date
                )],
                className="two columns"
            )
        ], className="row"),
        dcc.Graph(id='nap-time-bar-graph'),
        html.H2(children="Activity Notes"),
        html.Table(id='activity-table'),
        html.Div(id="data-div", style={"display": "none"})
    ])

    @cache.memoize()
    def cache_week_data(date) -> Dict:
        if app.config['TESTING']:
            return get_test_week_data()
        else:
            return get_week_data(date)

    @app.callback(
        dash.dependencies.Output('data-div', 'children'),
        [dash.dependencies.Input('date-picker-week', 'date')]
    )
    def compute_week_data(date):
        week_start = compute_week_start(date)
        cache_week_data(week_start)
        return week_start

    @app.callback(
        dash.dependencies.Output('nap-time-bar-graph', 'figure'),
        [dash.dependencies.Input('data-div', 'children')]
    )
    def update_nap_graph(date) -> Dict[str, Any]:
        """
        Plot sleep time
        """
        data = cache_week_data(date)

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

    @app.callback(
        dash.dependencies.Output('activity-table', 'children'),
        [dash.dependencies.Input('data-div', 'children')]
    )
    def update_activity_table(date):
        data = cache_week_data(date)
        return get_activty_table(data['Items'])

    return app
