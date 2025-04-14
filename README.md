# Trackie

Track your working time with [vim-outliner](https://github.com/vimoutliner/vimoutliner) as backend and write-frontend.
Using [rich](https://github.com/Textualize/rich) tables as read-frontend.

Your employer.otl schema where duration is an integer representing worked time in minutes:

```text
YYYY-MM-DD
    work description
	duration
YYYY-MM-DD
    work description
	duration
    work description
	duration
...
```

Output:

![Output of trackie](images/output.png)

trackie reads its config from a `.trackie.toml` in users home directory:

```toml
minutes_per_week = 480
minutes_per_day = 96
start_date = YYYY-MM-DD

[clients]
employer = "/path/to/foo.otl"

[abbr]
em = "employer name" # save keystrokes
```

Usage:
```bash
uv run wtrack --help
```
