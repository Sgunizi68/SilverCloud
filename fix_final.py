path = r'c:\projects\SilverCloud\app\templates\gelir_girisi.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Comprehensive cleanup of malformed Jinja2 tags in JS
c = c.replace('{{ gunler| length\n    }}', '{{ gunler|length }}')
c = c.replace('year: {{ d_year }\n    }', 'year: {{ d_year }}')
c = c.replace('month: { { d_month } }', 'month: {{ d_month }}')

# Also fix the one reported at 663 specifically
c = c.replace('year: {{ d_year }\n', 'year: {{ d_year }},\n')
# Just in case it's on one line
c = c.replace('year: {{ d_year }', 'year: {{ d_year }}')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print("Fix applied successfully via Python.")
