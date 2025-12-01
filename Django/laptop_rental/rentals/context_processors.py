from datetime import datetime

def global_year(request):
    year_list = list(range(2015, datetime.now().year + 1))
    selected_year = request.session.get("selected_year", 2025)

    return {
        "selected_year": int(selected_year),
        "year_list": year_list,
    }
