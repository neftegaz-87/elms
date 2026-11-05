---
title: "Installing RediSearch to enable fast E-commerce Search"
space: "ERPNext"
url: "https://docs.frappe.io/erpnext/installing_redisearch_to_enable_super_fast_e_commerce_search"
updated: "2026-03-02"
---


> **Experimental**
> 
> 

The E-Commerce module of ERPNext optionally uses RediSearch to enable search functionality which is configurable via **E Commerce Settings**.

Once installed and configured, RediSearch will be used to charge the search functionality of the E-Commerce website. This includes features like fuzzy-word searching, autocomplete, results ranking and customizable field indexing.

### Pre-requisites

1. Frappe Framework + ERPNext Setup
2. Redis 6+

### Installation Instructions


```
$ git clone --recursive https://github.com/RediSearch/RediSearch.git
$ cd RediSearch
$ sudo make setup # Remove `sudo` on macOS
$ make build
  

```

> Please Note: the latest version of RediSearch requires Redis 7.1+, while the stable redis as on 01-Aug-2023 available in snap repos is 7.0. Therefore, Redis need to be compiled from source for Redissearch to be compatible with Redis.
> 
> Also note ERPNext requires Redis 6+, therefore using Redis 7.1+ might break thinks. Use Redis 7.1+ with caution.
> 
> 

On successful completion of the above instructions, a `redisearch.so` binary file will be generated in the `RediSearch/build` directory.

Move this binary to the `/etc` directory and restart your Frappe Server:


```
sudo mv build/redisearch.so /etc/
  

```
Now, open the `redis_cache.conf` file located in the `config` directory (inside the bench directory). Add the following line before the `save ""` line and then restart bench server:


```
loadmodule /etc/redisearch.so
  

```
This will load the redisearch module at startup. You can check if the module was loaded successfully by running the following command in the `redis-cli -p 13000` (assuming port as 13000 default port for redis in frappe config):


```
> MODULE LIST
  

```
and `search` should be one of the modules.

You can also load the module on a running redis instance by running the following command in the `redis-cli`:


```
> MODULE LOAD /etc/redisearch.so
  

```

> We placed the `redisearch.so` module in the `/etc` directory, but it can be placed anywhere in the file system. We have used this directory because in the future the `loadmodule` line will be populated in the config file automatically and it will assume the binary is in the `/etc` directory.
> 
> 


> More detailed instructions can be found [here](https://github.com/RediSearch/redisearch-getting-started/blob/master/docs/002-install-redisearch.md).
> 
> 

