import pandas as pd


def construct_continental_files(
    path_to_data_file: str, path_to_country_code_map: str, scope: list[str]
):
    """For the continental scale, sometimes (e.g., in the minimal configuration) only a
    subset of countries is being considered. Due to such cases, we need to construct the
    continental data files by aggregating the data from national data files.
    1. extract national data file
    2. filter for countries being considered
    3. combine into a single continental value
    """

    df = pd.read_csv(path_to_data_file)
    country_code_map = pd.read_csv(path_to_country_code_map)

    # convert country names to codes
    country_code_map = country_code_map.set_index('name')['country_code'].to_dict()
    scope = [country_code_map[name] for name in scope]

    # filter for only the countries in scope
    df = df[df['id'].isin(scope)]

    pass


if __name__ == "__main__":
    # setup for prototyping ------------------------------------------------------------
    construct_continental_files(
        path_to_data_file="build/data/national/population.csv",
        path_to_country_code_map="build/data/national/units.csv",
        scope=["Ireland", "United Kingdom"],
    )
    # ----------------------------------------------------------------------------------
    # construct_continental_files(
    #     path_to_data_file=snakemake.input.data_file,
    #     scope=snakemake.params.scope,
    #     path_to_country_code_map=snakemake.input.locations
    # )
