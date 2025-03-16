from pathlib import Path
import tomllib


home = Path.home()
config_file = home / '.trackie.toml'
with config_file.open('rb') as f:
    config = tomllib.load(f)

MINUTES_PER_DAY = config['minutes_per_day']
MINUTES_PER_WEEK = config['minutes_per_week']
VIM_OTL_FILEPATH = config['vim_otl_filepath']
