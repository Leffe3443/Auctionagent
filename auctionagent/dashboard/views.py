from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Avg
from django.utils.dateparse import parse_datetime
from django.shortcuts import render


from django.conf import settings


from .models import AuctionScrapeRun, AuctionItem
from .dependencies.ai_parser import parse_ai_prompt, make_filter_fn

from django.contrib.auth.decorators import login_required


from .dependencies.pagesearch import scrape_auction
# Create your views here.

@login_required(login_url='/login/')
def return_datanadmin(request):
      # Items per run (last 10)
    runs = (AuctionScrapeRun.objects
            .order_by("-created_at")
            .values("id","created_at","items_found","duration_ms"))
    runs = list(reversed(list(runs)))  # chronological

    amount_objects = AuctionItem.objects.all().count()
    print(amount_objects)

    # Items ending soon buckets (<=24h, <=48h, <=72h) from latest runs
    from django.utils import timezone
    now = timezone.now()
    soon_24 = AuctionItem.objects.filter(ends_at__isnull=False, ends_at__lte=now + timezone.timedelta(hours=24)).count()
    soon_48 = AuctionItem.objects.filter(ends_at__isnull=False, ends_at__lte=now + timezone.timedelta(hours=48)).count()
    soon_72 = AuctionItem.objects.filter(ends_at__isnull=False, ends_at__lte=now + timezone.timedelta(hours=72)).count()

    # Currency mix
    currency_mix = (AuctionItem.objects
                    .values("currency")
                    .annotate(n=Count("id"))
                    .order_by("-n"))[:8]

   
    
    return render(request, 'stats_n_admin.html', {
                                              "runs": {
            "labels": [f'{r["created_at"].strftime("%H:%M")}' for r in runs],
            # "counts": [r["items_found"] for r in runs],
            "durations": [r["duration_ms"] for r in runs]
        },
        "endingSoon": {
            "labels": ["<=24h", "<=48h", "<=72h"],
            "counts": [soon_24, soon_48, soon_72]
        },
        "currency": {
            "labels": [c["currency"] or "—" for c in currency_mix],
            "counts": [c["n"] for c in currency_mix]
        },
        "amount_objects": amount_objects,})


# @login_required(login_url='/login/')
def return_dashboard(request):
    # Latest search results
    auction_items_latest = AuctionItem.objects.all()

    return render(request, "dashboard.html", {"auction_items_latest":auction_items_latest})

# @login_required(login_url='/login/')
def _persist_run(pages, items, duration_ms, prompt=""):
    run = AuctionScrapeRun.objects.create(
        pages=pages, items_found=len(items), duration_ms=duration_ms, prompt=prompt
    )
    for it in items:
        AuctionItem.objects.update_or_create(
            item_id=it["id"],
            defaults={
            'run':run,
            "item_id": it["id"],
            "title": it["title"],
            "url": it["url"],
            "info_text": it.get("info_text",""),
            "currency": it.get("currency","") or "",
            "current_bid": it.get("current_bid"),
            "ends_at": it.get("ends_at"),
            "estimate": it.get("estimate"),
            "location": it.get("location","") or "",
            "main_image_url": it.get("main_image_url")
            }
        )
    # AuctionItem.objects.bulk_create(bulk, ignore_conflicts=True)
    return run


@require_POST
# @login_required(login_url='/login/')
def run_auction_agent(request):
    pages = int(request.GET.get("pages", 2))    
    # Clocks, furniture etc
    category = request.GET.get("itemtype", "")
    sortingmethod = request.GET.get("sortingmethod", "")

    items, elapsed = scrape_auction(category, sortingmethod, pages=pages)
    # # Saving items scraped
    run = _persist_run(pages, items, elapsed)
    return JsonResponse({"run_id": run.id, "items": items})
    # return JsonResponse({})



import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime

from .dependencies.scrape_itemdetail import scrape_item_detail, search_similar_baseline
from .dependencies.ai_parser import web_search_with_openai  # stub you’ll implement


# Function gets triggerd when user writes prompt
from openai import OpenAI

# @login_required(login_url='/login/')
def ai_auction_agent(request):
    # user_request = request.GET.get("userRequest", "").strip()
    item_id = request.GET.get("itemid", "").strip()
    pages  = int(request.POST.get("pages", 3))
    # params = parse_ai_prompt(prompt, itemid)

    # print("User request:")
    # print(user_request)
    # print("________-")
    
    if not item_id:
        return JsonResponse({"error": "Missing item_id"}, status=400)

    # 1) scrape the reference item
    try:
        ref = scrape_item_detail(item_id)  # dict with title, info_text, images, currency, bid, ends_at, location, url
        # print("________________")
        # print("PRINT 'ref.title' variable:")
        # print("----")
        # print(ref['title'])
        # print(ref['info_text'])
        # print("################### End of ref ________________")
        item_title = ref['title']
        item_info = ref['info_text']
        # print(ref)
    except Exception as e:
        return JsonResponse({"error": f"Failed to scrape item {item_id}: {e}"}, status=500)

    # 2) system instructions from a text file
    # put your file at: app/prompts/auction_agent_system.txt
    try:
        from django.conf import settings
        import os
        prompt_path = os.path.join(settings.BASE_DIR, "dashboard", "prompts", "auction_agent_system.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_instructions = f.read()
    except Exception:
        system_instructions = "You are Auction Agent. Find similar items on auctionet.com. Return JSON with {id,title,url,images[],currency,current_bid,ends_at,location,info_text}."

    # 3) call OpenAI Web Search (stub: implement per latest OpenAI docs)
    # Pass the reference item + user_request + system instructions.
    try:
        print("System instructions: ", system_instructions)
        
        client = OpenAI(api_key=settings.OPENAI_KEY)
        # client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


        user_req_formulated = '\n' + "Find items similar to this: " + item_title + ' ' + item_info        


        resp = client.responses.create(
            model="gpt-4.1",
            input=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_req_formulated},
            ],
            tools=[{"type": "web_search"}],   # hosted tool
        )

        # 1) Plain text (if you still want it)
        ai_content_response = resp.output_text
       
    except Exception as e:
        # fallback: a simple baseline using your own scraper/search (optional)
        ai_content_response = {
            "summary": "Fallback: baseline likhetssökning (ingen AI).",
            "items": search_similar_baseline(ref, max_pages=2)
        }
    

    return JsonResponse({
        "reference": ref,                 # for debugging/UX
        "response_ai_content": ai_content_response,   
        # "items":   ai_out.get("items", []),      # array of {id,title,url,images[],currency,current_bid,ends_at,location,info_text}
        # "sources": ai_out.get("sources", []),    # optional: [{title,url,publisher,published_at}]
    # "reference": ref  # optional
        # "similar_items": ai_out.get("items", [])
    })

  
    # filter_fn = make_filter_fn(params)
    # items, elapsed = scrape_auction(pages=pages, filter_fn=filter_fn)
    # run = _persist_run(pages, items, elapsed, prompt=prompt)
    # return JsonResponse({
    #     "run_id": run.id,
    #     "parsed": params,
    #     "items": items
    # })

import time
def aifreesarch_auction_agent(request):
    object_type = request.GET.get("object_type", "").strip()
    userprompt_freesearch = request.GET.get("userprompt_freesearch", "").strip()



    response_ai_content = [
        'hello there hiasdfjlsfdfj'
        'hello there hiasdfjlsfdfj'
'hello there hiasdfjlsfdfj''hello there hiasdfjlsfdfj''hello there hiasdfjlsfdfj'
        'hello there hiasdfjlsfdfj'
        'hello there hiasdfjlsfdfj''hello there hiasdfjlsfdfj''hello there hiasdfjlsfdfj'
    ]

    # print("Object type:", object_type)
    # print("User prompt:", userprompt_freesearch)

      # 2) system instructions from a text file
    # put your file at: app/prompts/auction_agent_system.txt
    try:
        from django.conf import settings
        import os
        prompt_path = os.path.join(settings.BASE_DIR, "dashboard", "prompts", "freesearchagent.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_instructions = f.read()
    except Exception:
        system_instructions = "You are Auction Agent. Find similar items on auctionet.com. Return JSON with {id,title,url,images[],currency,current_bid,ends_at,location,info_text}."

    time.sleep(4)

    # 3) call OpenAI Web Search (stub: implement per latest OpenAI docs)
    # Pass the reference item + user_request + system instructions.
    # try:
        # print("System instructions: ", system_instructions)
        
        # client = OpenAI(api_key=settings.OPENAI_KEY)
        # # client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


        # # user_req_formulated = 'Object_type:' + object_type + '' + userprompt_freesearch        
        # user_req_formulated = ''

        # if object_type:
        #     user_req_formulated += 'Object type:' + object_type + '\n'

        # if userprompt_freesearch:
        #     user_req_formulated += "Instructions:" + userprompt_freesearch


        # print('User request: ', user_req_formulated)

        # resp = client.responses.create(
        #     model="gpt-4.1",
        #     input=[
        #         {"role": "system", "content": system_instructions},
        #         {"role": "user", "content": user_req_formulated},
        #     ],
        #     tools=[{"type": "web_search"}],   # hosted tool
        # )

        # # # 1) Plain text (if you still want it)
        # response_ai_content = resp.output_text
       
    # except Exception as e:
    #     # fallback: a simple baseline using your own scraper/search (optional)
    #     print("Pang")
    #     response_ai_content = {
    #         "summary": "Fallback: baseline likhetssökning (ingen AI).",
    #         # "items": search_similar_baseline(ref, max_pages=2)
    #     }
    
    
    return JsonResponse({
        "response_ai_content": response_ai_content,
    })



# Simple stats for Chart.js
# @login_required(login_url='/login/')
def auction_stats(request):
    # Items per run (last 10)
    runs = (AuctionScrapeRun.objects
            .order_by("-created_at")
            .values("id","created_at","items_found","duration_ms"))
    runs = list(reversed(list(runs)))  # chronological

    amount_objects = AuctionItem.objects.all().count()
    print(amount_objects)

    # Items ending soon buckets (<=24h, <=48h, <=72h) from latest runs
    from django.utils import timezone
    now = timezone.now()
    soon_24 = AuctionItem.objects.filter(ends_at__isnull=False, ends_at__lte=now + timezone.timedelta(hours=24)).count()
    soon_48 = AuctionItem.objects.filter(ends_at__isnull=False, ends_at__lte=now + timezone.timedelta(hours=48)).count()
    soon_72 = AuctionItem.objects.filter(ends_at__isnull=False, ends_at__lte=now + timezone.timedelta(hours=72)).count()

    # Currency mix
    currency_mix = (AuctionItem.objects
                    .values("currency")
                    .annotate(n=Count("id"))
                    .order_by("-n"))[:8]

    return JsonResponse({
        "runs": {
            "labels": [f'{r["created_at"].strftime("%H:%M")}' for r in runs],
            # "counts": [r["items_found"] for r in runs],
            "durations": [r["duration_ms"] for r in runs]
        },
        "endingSoon": {
            "labels": ["<=24h", "<=48h", "<=72h"],
            "counts": [soon_24, soon_48, soon_72]
        },
        "currency": {
            "labels": [c["currency"] or "—" for c in currency_mix],
            "counts": [c["n"] for c in currency_mix]
        },
        "amount_objects": amount_objects,
    })









# VALUATION SECTION

def return_valuation(request):
    return render(request, 'valuation.html')