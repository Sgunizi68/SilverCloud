path = r'c:\projects\SilverCloud\app\templates\gelir_girisi.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Fix the persistent Jinja/JS typos
c = c.replace('year: {{ d_year } }', 'year: {{ d_year }}')
c = c.replace('month: {{ d_month } }', 'month: {{ d_month }}')
c = c.replace('year: {{ d_year }}}', 'year: {{ d_year }}')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print("Fix applied successfully.")
