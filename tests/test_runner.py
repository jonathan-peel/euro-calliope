import sys
import yaml

import pytest
import calliope
import pandas as pd


def run_test(path_to_output, path_to_model, paths_to_cf_timeseries, config):
    exit_code = pytest.main(
        [
            f"--html={path_to_output}",
            f"--self-contained-html",
        ],
        plugins=[
            _create_config_plugin(
                path_to_model=path_to_model,
                paths_to_cf_timeseries=paths_to_cf_timeseries,
                config=config
            )
        ]
    )
    sys.exit(exit_code)


def _create_config_plugin(path_to_model, paths_to_cf_timeseries, config):
    """Creates fixtures from Snakemake configuration."""

    class SnakemakeConfigPlugin():

        @pytest.fixture(scope="function")
        def config(self):
            return dict(config)

        @pytest.fixture(scope="function", params=_read_scenario_names_from_yaml(path_to_model))
        def scenario(self, request):
            return request.param

        @pytest.fixture(scope="function")
        def model(self, scenario):
            return calliope.Model(path_to_model, scenario=scenario)

        @pytest.fixture(scope="function", params=paths_to_cf_timeseries)
        def capacity_factor_timeseries(self, request):
            return pd.read_csv(request.param, index_col=0, parse_dates=True)

    return SnakemakeConfigPlugin()


def _read_scenario_names_from_yaml(path_to_model):
    with open(path_to_model, 'r') as stream:
        model = yaml.safe_load(stream)
    return model["scenarios"].keys()


if __name__ == "__main__":
    run_test(
        path_to_model=snakemake.input.model,
        paths_to_cf_timeseries=snakemake.input.capacity_factor_timeseries,
        config=snakemake.params.config,
        path_to_output=snakemake.output[0]
    )