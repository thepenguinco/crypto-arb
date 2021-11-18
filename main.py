
from math import log
import requests
import concurrent.futures
import time
from decimal import *

# Executes currency arbitrage, returns possible arbitrage paths
def arbitrage(currencies, graph):
    res = []
    log_graph = [[-log(edge) for edge in row] for row in graph]
    # Pick any source vertex -- we can run Bellman-Ford from any vertex and
    # get the right result
    source = 0
    n = len(log_graph)
    min_dist = [float('inf')] * n
    pre = [-1] * n
    min_dist[source] = 0

    # Relax edges |V - 1| times
    for i in range(n-1):
            for src in range(n):
                for dst in range(n):
                    if min_dist[dst] > min_dist[src] + log_graph[src][dst]:
                        min_dist[dst] = min_dist[src] + log_graph[src][dst]
                        pre[dst] = src
    # Find the negative cycles and return them
    for src in range(n):
        for dst in range(n):
            possible_arb = []
            if min_dist[dst] > min_dist[src] + log_graph[src][dst]:
                print_cycle = [dst, src]
                while pre[src] not in print_cycle:
                    print_cycle.append(pre[src])
                    src = pre[src]
                print_cycle.append(pre[src])
                seen = set()
                for p in print_cycle[::-1]:
                    possible_arb.append(currencies[p])
                    if p in seen:
                        break
                    seen.add(p)
                res.append(possible_arb)
    return res

def get_ids(json):
    ids = []
    for fx in json:
        ids.append(fx["id"])
    return ids

def load_url(id, timeout):
    return requests.get(f"https://api.exchange.coinbase.com/products/{id}/book", timeout = timeout)

if __name__ == "__main__":
    url = "https://api.exchange.coinbase.com/products"
    headers = {"Accept": "application/json"}
    response = requests.request("GET", url, headers=headers)
    json = response.json()
    a = map(lambda x : x["base_currency"], json)
    b = map(lambda x : x["quote_currency"], json)
    currencies = list(set(a).union(set(b)))
    currencymap = dict(map(lambda x: (x[1], x[0]), enumerate(currencies)))
    print(currencymap)
    rates = [[float('inf') for j in range(len(currencymap))] for i in range(len(currencymap))]
    for i in range(len(currencies)):
        rates[i][i] = 1
    while True:
        time.sleep(2)
        headers = {"Accept": "application/json"}
        # doesn't quite work...
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_to_url = {executor.submit(load_url, id, 4): id for id in get_ids(json)}
            for future in concurrent.futures.as_completed(future_to_url):
                pair = future_to_url[future]
                try:
                    data = future.result().json()
                    pair = pair.split('-')
                    #print(data)
                    print(pair)
                    # TODO something with amount later
                    # quote currency => base currency bid price
                    if Decimal(data["bids"][0][0]) != 0.0:
                        rates[currencymap[pair[1]]][currencymap[pair[0]]] = Decimal(data["bids"][0][0])
                    # base currency => quote currency ask price (take inverse)
                    rates[currencymap[pair[0]]][currencymap[pair[1]]] = 1/Decimal(data["asks"][0][0])
                except Exception as exc:
                    print(exc)
        print(rates)
        print(arbitrage(currencies, rates))

