import http.client
import json

conn = http.client.HTTPSConnection("api.apyhub.com")

text = (
    "How Will Dow Futures Open As Trump Adds 100% China Tariff? Oracle, Tesla, Taiwan Semi In Focus: "
    "The stock market tumbled with President Trump imposing huge China tariffs after the close. "
    "Oracle, JPMorgan, Taiwan Semi are on tap. Is Tesla's chart healthy?\n"
    "What's the End of the EV Tax Credit Mean for Tesla? Listen to Elon Musk: "
    "A key advantage for EVs is going away.\n"
    "Tesla’s top-compensated executives & directors besides Elon Musk: "
    "Quick facts …"
    # add the rest of your text here…
)

payload_obj = {
    "text": text,
    "summary_length": "short",
    "output_language": "en"
}

payload = json.dumps(payload_obj, ensure_ascii=False).encode("utf-8")

headers = {
    "Content-Type": "application/json; charset=utf-8",
    "apy-token": "token"
}

conn.request("POST", "/ai/summarize-text", body=payload, headers=headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8", errors="replace"))
