# Stocks management system

This project ccombines Django and Interactive Brokers API to manage stocks portfolio.

# AWS

account: kadimagrouppanama@gmail.com

# Server

ssh -i kadima_aws.pem ubuntu@3.15.26.164

# IP

http://3.15.26.164:8001/

## Capabilities include:

- Connecting to the IB API
- Managing the addition and the deletion of stocks from the list.
- Adding to history page on which there is an option to make some transactions P/L calculations

## Data sources APIs

- yFinance: https://github.com/ranaroussi/yfinance (yf)
  > Need to install yFinance with:

pip install yfinance --upgrade --no-cache-dir

## Latest Python sources

https://interactivebrokers.github.io/#

## Important TWS docs locatios:

Installation: https://dimon.ca/how-to-setup-ibc-and-tws-on-headless-ubuntu-in-10-minutes/
Tick types: https://interactivebrokers.github.io/tws-api/tick_types.html#ib_dividends
EClient: https://tinyurl.com/y73tg4t8
EWrapper: https://tinyurl.com/y8t2ujfp
Basic Orders examples: https://interactivebrokers.github.io/tws-api/basic_orders.html
Tick data: https://interactivebrokers.github.io/tws-api/tick_data.html

# Exporting table to CSV file

https://www.youtube.com/watch?v=lE8SXffJUmI

# VNC Issues

- https://itectec.com/unixlinux/make-sure-x-server-isnt-already-running/
- https://unix.stackexchange.com/questions/232749/xvfb-screen-cannot-establish-any-listening-sockets-make-sure-an-x-server

# Gunicorn settings

### Increase Gunicorn workers timeouts

- https://medium.com/building-the-system/gunicorn-3-means-of-concurrency-efbb547674b7

# Nginx - Timeouts increase

- https://ubiq.co/tech-blog/increase-request-timeout-nginx/
