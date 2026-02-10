
import openpyxl
from django.http import HttpResponse
from datetime import datetime

def export_to_excel(queryset, filename, columns, headers=None):
    """
    Exports a queryset to an Excel file.
    
    :param queryset: Django QuerySet to export
    :param filename: Name of the generated file (without extension)
    :param columns: List of model field names or callable functions to retrieve data
                    Supports dot notation for related fields (e.g. 'category.name')
    :param headers: List of column headers (optional, defaults to columns)
    """
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response['Content-Disposition'] = f'attachment; filename={filename}_{timestamp}.xlsx'
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Export"
    
    # Write Header
    if headers:
        ws.append(headers)
    else:
        ws.append([c.replace('_', ' ').title() for c in columns])
        
    def get_value(obj, attr_path):
        """Helper to get nested attribute value"""
        current = obj
        for part in attr_path.split('.'):
            if current is None:
                return ''
            
            if hasattr(current, part):
                current = getattr(current, part)
                if callable(current):
                    # Check if it's a manager or method
                    try:
                        current = current()
                    except:
                        pass # Requires arguments or other issue
            elif isinstance(current, dict):
                 current = current.get(part)
            else:
                return ''
        return current

    # Write Data
    for obj in queryset:
        row = []
        for col in columns:
            val = get_value(obj, col)
            
            # Formatting
            if isinstance(val, datetime):
                if val.tzinfo is not None:
                     val = val.replace(tzinfo=None) # Strip timezone
            elif val is None:
                val = ''
            else:
                val = str(val) # Convert to string for safety
                
            row.append(val)
        ws.append(row)
        
    wb.save(response)
    return response
