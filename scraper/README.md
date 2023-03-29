# Website Scraping Helper
## Configuration
Individual websites to be scraped are configured in `config.yaml`

## Scraping

`base_spider.py` defines the spider factory. It can be modified to add additional scraping parameters, and to modify an existing parameter, use the `config.yaml`.
`runner.py` users the spider_factory to generate a spider based on a string typed into `runner.py`, feeding it a specific config file

## Output
A `base_spider.log` is produced when the scraper is run. This is currently overwritten each time.
`runner.py` has a line that runs a main function from `generate_logfile_csv.py`. This creates the desired csv output.
The logfile is supplemented with more seperable urls, which are then set()ed and sorted.
