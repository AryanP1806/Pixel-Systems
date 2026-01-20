from datetime import datetime

def global_year_context(request):
    """
    Makes 'selected_year' available globally as an INTEGER.
    """
    current_year = datetime.now().year
    
    # 1. Get raw value from session
    raw_year = request.session.get('selected_year', current_year)
    
    # 2. Force conversion to int (handles string "2024" -> int 2024)
    try:
        selected_year = int(raw_year)
    except (ValueError, TypeError):
        selected_year = current_year # Fallback if data is corrupted

    return {
        'selected_year': selected_year,  # Now strictly an Int
        'year_list': range(2015, current_year + 1),
    }