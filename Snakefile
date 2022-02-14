import glob
from pathlib import Path

from snakemake.utils import validate

configfile: "config/default.yaml"
validate(config, "config/schema.yaml")

root_dir = config["root-directory"] + "/" if config["root-directory"] not in ["", "."] else ""
__version__ = open(f"{root_dir}VERSION").readlines()[0].strip()
script_dir = f"{root_dir}scripts/"
test_dir = f"{root_dir}tests/"
model_test_dir = f"{test_dir}model"
template_dir = f"{root_dir}templates/"
model_template_dir = f"{template_dir}models/"
techs_template_dir = f"{model_template_dir}techs/"

include: "./rules/shapes.smk"
include: "./rules/wind-and-solar.smk"
include: "./rules/biofuels.smk"
include: "./rules/hydro.smk"
include: "./rules/transmission.smk"
include: "./rules/demand.smk"
include: "./rules/sync.smk"
localrules: all, clean
wildcard_constraints:
        resolution = "continental|national|regional"

onstart:
    shell("mkdir -p build/logs")
onsuccess:
     if "email" in config.keys():
         shell("echo "" | mail -s 'euro-calliope succeeded' {config[email]}")
onerror:
     if "email" in config.keys():
         shell("echo "" | mail -s 'euro-calliope failed' {config[email]}")


rule all:
    message: "Generate euro-calliope pre-built models and run tests."
    input:
        "build/logs/continental/test-report.html",
        "build/logs/national/test-report.html",
        "build/models/continental/example-model.yaml",
        "build/models/national/example-model.yaml",
        "build/models/regional/example-model.yaml",
        "build/models/build-metadata.yaml"


rule all_tests:
    message: "Generate euro-calliope pre-built models and run all tests."
    input:
        "build/models/continental/example-model.yaml",
        "build/models/national/example-model.yaml",
        "build/models/regional/example-model.yaml",
        "build/logs/continental/test-report.html",
        "build/logs/national/test-report.html",
        "build/logs/regional/test-report.html",
        "build/models/build-metadata.yaml"


rule simple_techs_and_locations_template:
    message: "Create {wildcards.resolution} tech definition file `{wildcards.template}` from template."
    input:
        script = script_dir + "template_techs.py",
        template = techs_template_dir + "{template}",
        locations = rules.locations_template.output.csv
    params:
        scaling_factors = config["scaling-factors"],
    wildcard_constraints:
        template = "supply/load-shedding.yaml|storage/electricity.yaml"
    conda: "envs/default.yaml"
    output: "build/models/{resolution}/techs/{template}"
    script: "scripts/template_techs.py"


rule no_params_model_template:
    message: "Create {wildcards.resolution} configuration files from templates where no parameterisation is required."
    input:
        template = model_template_dir + "{template}",
    output: "build/models/{resolution}/{template}"
    wildcard_constraints:
        template = "interest-rate.yaml|scenarios.yaml"
    conda: "envs/shell.yaml"
    shell: "cp {input.template} {output}"


rule no_params_template:
    message: "Create non-model files from templates where no parameterisation is required."
    input:
        template = template_dir + "{template}",
    output: "build/models/{template}"
    wildcard_constraints:
        template = "[^/]*"
    conda: "envs/shell.yaml"
    shell: "cp {input.template} {output}"


rule model_template:
    message: "Generate top-level {wildcards.resolution} model configuration file from template"
    input:
        script = script_dir + "template_model.py",
        template = model_template_dir + "example-model.yaml",
        non_model_files = expand(
            "build/models/{template}", template=["environment.yaml", "README.md"]
        ),
        input_files = expand(
            "build/models/{{resolution}}/{input_file}",
            input_file=[
                "interest-rate.yaml",
                "locations.yaml",
                "scenarios.yaml",
                "techs/demand/electricity.yaml",
                "techs/storage/electricity.yaml",
                "techs/storage/hydro.yaml",
                "techs/supply/biofuel.yaml",
                "techs/supply/hydro.yaml",
                "techs/supply/load-shedding.yaml",
                "techs/supply/open-field-solar-and-wind-onshore.yaml",
                "techs/supply/rooftop-solar.yaml",
                "techs/supply/wind-offshore.yaml",
            ]
        ),
        optional_input_files = lambda wildcards: expand(
            f"build/models/{wildcards.resolution}/{{input_file}}",
            input_file=[
                "techs/transmission/electricity-linked-neighbours.yaml",
            ] + ["techs/transmission/electricity-entsoe.yaml" for i in [None] if wildcards.resolution == "national"]
        )
    params:
        year = config["scope"]["temporal"]["first-year"]
    conda: "envs/default.yaml"
    output: "build/models/{resolution}/example-model.yaml"
    script: "scripts/template_model.py"


rule build_metadata:
    message: "Generate build metadata."
    input:
        script_dir + "metadata.py",
        "build/models/continental/example-model.yaml",
        "build/models/national/example-model.yaml",
        "build/models/regional/example-model.yaml",
    params:
        config = config,
        version = __version__
    output: "build/models/build-metadata.yaml"
    conda: "envs/default.yaml"
    script: "scripts/metadata.py"


rule clean: # removes all generated results
    shell:
        """
        rm -r build/
        echo "Data downloaded to data/automatic/ has not been cleaned."
        """


rule test:
    message: "Run tests"
    input:
        test_dir = model_test_dir,
        tests = map(str, Path(model_test_dir).glob("**/test_*.py")),
        example_model = "build/models/{resolution}/example-model.yaml",
        capacity_factor_timeseries = expand(
            "build/models/{{resolution}}/timeseries/supply/capacityfactors-{technology}.csv",
            technology=ALL_WIND_AND_SOLAR_TECHNOLOGIES + ["hydro-ror", "hydro-reservoir-inflow"]
        )
    params:
        config = config,
        override_dict = lambda wildcards: config["test"]["overrides"][wildcards.resolution],
        scenarios = lambda wildcards: config["test"]["scenarios"][wildcards.resolution],
        subset_time = lambda wildcards: config["test"]["subset_time"][wildcards.resolution],
    output: "build/logs/{resolution}/test-report.html"
    conda: "./envs/test.yaml"
    script: "./tests/model/test_runner.py"
