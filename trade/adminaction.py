
import csv
from django.http import HttpResponse, FileResponse
import pandas as pd


def export_as_csv_action(description="Export selected objects as CSV file", fields=None,):
    def export_as_csv(modeladmin, request, queryset):
        opts = modeladmin.model._meta
        
        field_names = [field for field in fields]
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % str(opts).replace('.', '_')

        writer = csv.writer(response)

        writer.writerow(list(field_names))
            
        for obj in queryset:
            row = []
            for field in fields:
                if hasattr(obj, field):
                    value = getattr(obj, field)
                elif hasattr(modeladmin, field):
                    value = getattr(modeladmin, field)(obj)
                else:
                    value = None
                row.append(value)
            writer.writerow(row)
        return response

    export_as_csv.short_description = description
    return export_as_csv