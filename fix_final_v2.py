path = r'c:\projects\SilverCloud\app\templates\gelir_girisi.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Fix the triple brace and any other small typos in the requestData block
c = c.replace('year: {{ d_year }}},', 'year: {{ d_year }},')
c = c.replace('year: {{ d_year }}}', 'year: {{ d_year }}') # just in case
c = c.replace('year: {{ d_year } }', 'year: {{ d_year }}')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print("Final cleanup applied successfully.")
