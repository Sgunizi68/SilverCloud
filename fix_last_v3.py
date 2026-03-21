import os

path = r'c:\projects\SilverCloud\app\templates\gelir_girisi.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Highly specific targeted replacement for the broken requestData block
broken_block = """            sube_id: branchSelect ? branchSelect.value : '{{ secili_sube_id }}',
            year: {{ d_year }
    },
    month: { { d_month } },
    payload: payloadToSave"""

fixed_block = """            sube_id: branchSelect ? branchSelect.value : '{{ secili_sube_id }}',
            year: {{ d_year }},
            month: {{ d_month }},
            payload: payloadToSave"""

if broken_block in c:
    c = c.replace(broken_block, fixed_block)
    print("Broken block found and replaced.")
else:
    print("Broken block NOT found exactly. Trying regex or parts.")
    # Fallback to parts if whitespace differs
    c = c.replace('year: {{ d_year }\n    }', 'year: {{ d_year }}')
    c = c.replace('month: { { d_month } }', 'month: {{ d_month }}')
    c = c.replace('year: {{ d_year } }', 'year: {{ d_year }}')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print("Final cleanup attempt finished.")
