"""Remixes NUTS, LAU, and GADM data to form the units of the analysis."""

import fiona
import geopandas as gpd
import pandas as pd
import pycountry

DRIVER = "GeoJSON"


def remix_units(
    path_to_nuts, path_to_gadm, path_to_output, layer_name, layer_config, all_countries
):
    """Remixes NUTS, LAU, and GADM data to form the units of the analysis.
    source_layers: a dict with keys as each geographical layer type (nutsX or gadmnX)
    and values as a geodataframe of the POLYGONS
    """
    source_layers = _read_source_layers(path_to_nuts, path_to_gadm)
    _validate_source_layers(source_layers)
    _validate_layer_config(all_countries, layer_config, layer_name)
    layer = _build_layer(layer_config, source_layers)
    _validate_layer(layer, layer_name, all_countries)
    if layer_name == "continental":  # treat special case
        layer = _continental_layer(layer)
    _write_layer(layer, path_to_output)


def _read_source_layers(path_to_nuts, path_to_gadm):
    source_layers = {
        layer_name: gpd.read_file(path_to_nuts, layer=layer_name)
        for layer_name in fiona.listlayers(path_to_nuts)
    }
    source_layers.update({
        layer_name: gpd.read_file(path_to_gadm, layer=layer_name)
        for layer_name in fiona.listlayers(path_to_gadm)
    })
    return source_layers


def _validate_source_layers(source_layers):
    crs = [layer.crs for layer in source_layers.values()]
    assert not crs or crs.count(crs[0]) == len(
        crs
    ), "Source layers have different crs. They must match."


def _validate_layer_config(all_countries, layer_config, layer_name):
    assert all(country in layer_config for country in all_countries), (
        f"Layer {layer_name} is not correctly " "defined."
    )


def _build_layer(country_to_source_map, source_layers):
    crs = [layer.crs for layer in source_layers.values()][0]
    layer = pd.concat([
        source_layers[source_layer][
            source_layers[source_layer].country_code == _iso3(country)
        ]
        for country, source_layer in country_to_source_map.items()
    ])
    assert isinstance(layer, pd.DataFrame)
    return gpd.GeoDataFrame(layer, crs=crs)


def _validate_layer(layer, layer_name, countries):
    assert all(
        _iso3(country) in layer.country_code.unique() for country in countries
    ), f"Countries are missing in layer {layer_name}."


def _iso3(country_name):
    return pycountry.countries.lookup(country_name).alpha_3


def _continental_layer(layer):
    # special case all Europe
    layer = layer.dissolve(by=[1 for idx in layer.index])
    index = layer.index[0]
    layer.loc[index, "id"] = "EUR"
    layer.loc[index, "country_code"] = "EUR"
    layer.loc[index, "name"] = "Europe"
    layer.loc[index, "type"] = "continent"
    layer.loc[index, "proper"] = 1
    return layer


def _write_layer(gdf, path_to_file):
    gdf.to_file(path_to_file, driver=DRIVER)


if __name__ == "__main__":
    # DUBUG CONFIGURATION
    # ----------------------------------------------------------------------------------
    # path_to_nuts = "build/data/administrative-borders-nuts.gpkg"
    # path_to_gadm = "build/data/administrative-borders-gadm.gpkg"
    # path_to_output = "build/data/regional/units.geojson"
    # layer_name = "regional"
    # all_countries = ["Ireland", "United Kingdom"]
    # layer_config = {
    #     "Ireland": "gadm1",
    #     "United Kingdom": "gadm1",
    #     "Austria": "gadm1",
    #     "Belgium": "gadm1",
    #     "Bulgaria": "gadm1",
    #     "Croatia": "gadm1",
    #     "Cyprus": "gadm1",
    #     "Czech Republic": "gadm1",
    #     "Denmark": "gadm1",
    #     "Estonia": "gadm1",
    #     "Finland": "gadm1",
    #     "France": "gadm1",
    #     "Germany": "gadm1",
    #     "Greece": "gadm1",
    #     "Hungary": "gadm1",
    #     "Italy": "gadm1",
    #     "Latvia": "gadm1",
    #     "Lithuania": "gadm1",
    #     "Luxembourg": "gadm2",
    #     "Netherlands": "gadm1",
    #     "Poland": "gadm1",
    #     "Portugal": "gadm1",
    #     "Romania": "gadm1",
    #     "Slovakia": "gadm1",
    #     "Slovenia": "gadm1",
    #     "Spain": "gadm1",
    #     "Sweden": "gadm1",
    #     "Albania": "gadm1",
    #     "Bosnia and Herzegovina": "gadm1",
    #     "Macedonia, Republic of": "nuts3",
    #     "Montenegro": "gadm1",
    #     "Norway": "gadm1",
    #     "Serbia": "gadm1",
    #     "Switzerland": "gadm1",
    # }

    # remix_units(
    #     path_to_nuts=path_to_nuts,
    #     path_to_gadm=path_to_gadm,
    #     path_to_output=path_to_output,
    #     layer_name=layer_name,
    #     all_countries=all_countries,
    #     layer_config=layer_config,
    # )
    # ----------------------------------------------------------------------------------

    # breakpoint()

    layer_name = snakemake.wildcards[0]
    remix_units(
        path_to_nuts=snakemake.input.nuts,
        path_to_gadm=snakemake.input.gadm,
        path_to_output=snakemake.output[0],
        layer_name=layer_name,
        all_countries=snakemake.params.all_countries,
        layer_config=snakemake.params.layer_configs[layer_name],
    )
