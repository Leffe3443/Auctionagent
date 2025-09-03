import re, datetime as dt

def parse_ai_prompt(prompt, itemid):

    print("Prompt", prompt)
    print("Item id:", itemid)
    
    # return {
    #     "max_price": max_price,
    #     "ends_within_days": ends_days,
    #     "include_tokens": include_tokens
    # }

def make_filter_fn(params: dict):
    import datetime as dt
    max_price = params.get("max_price")
    ends_days = params.get("ends_within_days")
    tokens    = [t.lower() for t in params.get("include_tokens", [])]

    def _fn(item):
        ok = True
        if max_price is not None and item.get("current_bid") is not None:
            ok &= (item["current_bid"] <= max_price)
        if ends_days is not None and item.get("ends_at"):
            try:
                ends = dt.datetime.fromisoformat(item["ends_at"])
                ok &= (ends <= dt.datetime.utcnow().replace(tzinfo=ends.tzinfo) + dt.timedelta(days=ends_days))
            except Exception:
                pass
        if tokens:
            hay = f'{item.get("title","")} {item.get("info_text","")}'.lower()
            ok &= all(t in hay for t in tokens)
        return ok

    return _fn


# app/openai_bridge.py
def web_search_with_openai(system_instructions: str, user_request: str, reference_item: dict) -> dict:
    """
    Implement this with OpenAI’s official SDK / Responses API + Web Search tool.
    Return a dict:
    {
      "summary": "string",
      "items": [ {id,title,url,images[],currency,current_bid,ends_at,location,info_text}, ... ]
    }
    """
    # Pseudocode:
    # from openai import OpenAI
    # client = OpenAI(api_key=...)
    # prompt = f"""
    # SYSTEM:
    # {system_instructions}
    #
    # USER:
    # Reference item JSON:
    # {json.dumps(reference_item, ensure_ascii=False)}
    #
    # Task: {user_request}
    # Return ONLY JSON with keys: summary, items (array of the specified shape).
    # """
    # resp = client.responses.create(model="gpt-4o-mini", tools=[{"type":"web_search"}], input=prompt)
    # parse tool output / text to dict safely
    # return parsed_dict
    raise NotImplementedError("Implement with OpenAI Web Search per official docs.")
