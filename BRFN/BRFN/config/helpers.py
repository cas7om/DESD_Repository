import datetime as dt
import json
from math import sin, cos, radians, acos
from urllib.request import urlopen
from urllib.error import URLError

from applications.account_management.models import User
from config.constants import SESSION_USER_ID_KEY


EARTH_RADIUS_IN_MILES = 3958.8
GEOCODE_API = "https://api.postcodes.io/postcodes/"


def get_week_start_end():
    today = dt.date.today()
    week_start = today - dt.timedelta(days=today.weekday())
    week_end = week_start + dt.timedelta(days=7)
    return week_start, week_end


def current_user_light(request):
    user_id = request.session.get(SESSION_USER_ID_KEY)
    if not user_id:
        return None
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None


def current_user(request):
    user_id = request.session.get(SESSION_USER_ID_KEY)
    user = None
    if user_id:
        user = User.objects.filter(id=user_id).first()
        return {
            "current_user": user,
            "is_logged_in": user is not None,
            "is_admin": user.has_role("Admin"),
            "is_producer": user.has_role("Producer"),
            "is_customer": user.has_role("Customer"),
        }
    return {
        "current_user": user,
        "is_logged_in": user is not None,
        "is_admin": False,
        "is_producer": False,
        "is_customer": False,
    }


def geocode_postcode(postcode):
    postcode = postcode.replace(" ", "").upper()
    try:
        with urlopen(f"{GEOCODE_API}{postcode}") as response:
            data = json.loads(response.read().decode("utf-8"))
    except URLError:
        return None
    except Exception:
        return None

    if data.get("status") != 200:
        return None

    result = data["result"]
    return result["latitude"], result["longitude"]


def calc_distance(coords_a, coords_b):
    lat_a, long_a = coords_a
    lat_b, long_b = coords_b
    lat_a = radians(lat_a)
    lat_b = radians(lat_b)
    delta_long = radians(long_a - long_b)
    cos_x = (
        sin(lat_a) * sin(lat_b) +
        cos(lat_a) * cos(lat_b) * cos(delta_long)
    )
    return acos(cos_x) * EARTH_RADIUS_IN_MILES