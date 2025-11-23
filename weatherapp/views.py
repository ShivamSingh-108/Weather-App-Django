# weatherapp/views.py
from django.shortcuts import render
from django.contrib import messages
import requests
import datetime
import os

def home(request):
    # --- get city from POST (or default) ---
    if 'city' in request.POST:
        city = request.POST['city']
    else:
        city = 'indore'

    # --- load API keys (use environment variables or set directly here) ---
    OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', '')  # set this in your environment or paste the key here
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')            # set this if you want image search
    SEARCH_ENGINE_ID = os.environ.get('SEARCH_ENGINE_ID', '')        # Google Custom Search CX

    # --- prepare OpenWeather request properly using params ---
    weather_url = 'https://api.openweathermap.org/data/2.5/weather'
    PARAMS = {
        'q': city,
        'units': 'metric',
        'appid': OPENWEATHER_API_KEY
    }

    # Default values
    image_url = ""
    day = datetime.date.today()

    try:
        # --- fetch weather data ---
        weather_resp = requests.get(weather_url, params=PARAMS, timeout=5)
        weather_resp.raise_for_status()  # raise for HTTP errors
        wdata = weather_resp.json()

        # --- extract weather info (may raise KeyError if API returns unexpected data) ---
        description = wdata['weather'][0]['description']
        icon = wdata['weather'][0]['icon']
        temp = wdata['main']['temp']

        # --- attempt Google Custom Search image fetch (non-fatal) ---
        if GOOGLE_API_KEY and SEARCH_ENGINE_ID:
            try:
                query = f"{city} 1920x1080"
                page = 1
                start = (page - 1) * 10 + 1
                # note: searchType=image (not "image" vs earlier) and we keep same imgSize param
                city_url = (
                    f"https://www.googleapis.com/customsearch/v1"
                    f"?key={GOOGLE_API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}"
                    f"&start={start}&searchType=image&imgSize=xlarge"
                )
                img_resp = requests.get(city_url, timeout=5)
                if img_resp.status_code == 200:
                    gdata = img_resp.json()
                    # defensive extraction of returned items
                    search_items = gdata.get("items") if isinstance(gdata, dict) else None
                    if isinstance(search_items, list) and len(search_items) > 0:
                        idx = 1 if len(search_items) > 1 else 0
                        item = search_items[idx]
                        if isinstance(item, dict):
                            image_url = item.get("link") or item.get("url") or item.get("thumbnail") or ""
                # if non-200, we silently skip and keep image_url empty
            except requests.RequestException as ie:
                # network error for image fetch — log for debugging, but do not crash
                print("Image fetch network error:", ie)
                image_url = ""
            except Exception as ie:
                print("Unexpected image fetch error:", ie)
                image_url = ""
        else:
            # Google keys not provided — skip image fetch (safe)
            image_url = ""

        # --- render the successful page ---
        return render(
            request,
            'weatherapp/index.html',
            {
                'description': description,
                'icon': icon,
                'temp': temp,
                'day': day,
                'city': city,
                'exception_occurred': False,
                'image_url': image_url
            }
        )

    except KeyError:
        # API returned data but with an unexpected structure (e.g., city not found)
        exception_occurred = True
        messages.error(request, 'Entered data is not available to API')

        # fallback values (keeps original behavior you had)
        return render(
            request,
            'weatherapp/index.html',
            {
                'description': 'clear sky',
                'icon': '01d',
                'temp': 25,
                'day': day,
                'city': 'indore',
                'exception_occurred': exception_occurred,
                'image_url': ""  # no image in fallback
            }
        )

    except requests.RequestException as re:
        # network-level error contacting OpenWeather
        print("Weather API network error:", re)
        exception_occurred = True
        messages.error(request, 'Network error while contacting Weather API')

        return render(
            request,
            'weatherapp/index.html',
            {
                'description': 'clear sky',
                'icon': '01d',
                'temp': 25,
                'day': day,
                'city': 'indore',
                'exception_occurred': exception_occurred,
                'image_url': ""
            }
        )

    except Exception as e:
        # catch-all to avoid crashing the page
        print("Unexpected error in home view:", e)
        exception_occurred = True
        messages.error(request, 'An unexpected error occurred')

        return render(
            request,
            'weatherapp/index.html',
            {
                'description': 'clear sky',
                'icon': '01d',
                'temp': 25,
                'day': day,
                'city': 'indore',
                'exception_occurred': exception_occurred,
                'image_url': ""
            }
        )
