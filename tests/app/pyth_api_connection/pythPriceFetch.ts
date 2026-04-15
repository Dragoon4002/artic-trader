const url = 'https://pyth-lazer.dourolabs.app/v1/latest_price';

const headers = {
  'Authorization': 'Bearer CXLuq3DmK2mQjkYMDAz99LkKM8WrugQYLbsKfJ2EbdWR',
  'Content-Type': 'application/json'
};

type ResponseData = {
  "parsed": {
    timestampUs: number,
    priceFeeds: {priceFeedId: number, price: string}[]
  },
  "evm": any
}

const Tokens = [
  ["Bitcoin", "BTC"],
  ["Ethereum", "ETH"],
  ["Solana", "SOL"],
  ["Cardano", "ADA"],
  ["Polkadot", "DOT"],
  ["Avalanche", "AVAX"],
  ["Chainlink", "LINK"],
  ["Polygon", "MATIC"],
  ["Cosmos", "ATOM"],
  ["Algorand", "ALGO"]
]

const body = {
  "channel": "fixed_rate@200ms",
  "formats": ["evm"],
  "properties": ["price"],
  "symbols": Tokens.map(([_, symbol]) => `Crypto.${symbol}/USD`),
  "parsed": true,
  "jsonBinaryEncoding": "hex"
};

const priceFeed = fetch(url, {
  method: 'POST',
  headers: headers,
  body: JSON.stringify(body)
});

priceFeed
  .then(response => {
    if (!response.ok) {
      throw new Error('Network response was not ok ' + response.statusText);
    }
    return response.json();
  })
  .then(data => {
    console.log(data.parsed.priceFeeds.map((feed: {priceFeedId: number, price: string}, index: number) => {
      const symbol = Tokens[index][1];
      const price = parseFloat(feed.price) * 10 ** -8;
      return [symbol, price.toFixed(2)];
    }));
  })
  .catch(error => {
    console.error('There has been a problem with your fetch operation:', error);
  });