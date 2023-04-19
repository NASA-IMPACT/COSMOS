# Website Scraping Helper
## Configuration
Individual websites to be scraped are configured in `config.yaml`

## Running the Scraper
To run it go to `sde_scraper` and run `python runner.py <config website name>`, using the name you defined in config.yaml. This will generate a final output file in `processed_csvs/<config website name>.csv'`

## Scraping

`base_spider.py` defines the spider factory. It can be modified to add additional scraping parameters, and to modify an existing parameter, use the `config.yaml`.
`runner.py` users the spider_factory to generate a spider based on a string typed into `runner.py`, feeding it a specific config file

## Output
A `<config website name>.log` is produced when the scraper is run.
`runner.py` has a line that runs a main function from `generate_logfile_csv.py`. This creates the desired csv output.
The logfile is supplemented with more seperable urls, which are then set()ed and sorted.

## Tmux
When you want to run the script multiple times, you can use tmux.
`tmux new-session -s <session_name>`
`tmux list-sessions`
`tmux attach-session -t <session_name>`
Detach from the session by pressing command-b followed by d. Your script will continue to run in the background within the tmux session.
