import os

path = r'c:\projects\SilverCloud\app\templates\gelir_girisi.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update calculateTotals outputs
c = c.replace('colSatis.innerText = gunlukSatis.toFixed(2);', 'colSatis.innerText = formatMoney(gunlukSatis);')
c = c.replace('colFark.innerText = fark.toFixed(2);', 'colFark.innerText = formatMoney(fark);')
c = c.replace('elSatisAylik.innerText = aylikToplamSatis.toFixed(2);', 'elSatisAylik.innerText = formatMoney(aylikToplamSatis);')
c = c.replace('elFarkAylik.innerText = aylikFark.toFixed(2);', 'elFarkAylik.innerText = formatMoney(aylikFark);')

# 2. Fix the broken requestData block AGAIN
broken_block = """            sube_id: branchSelect ? branchSelect.value : '{{ secili_sube_id }}',
            year: {{ d_year }
    },
    month: { { d_month } },"""

fixed_block = """            sube_id: branchSelect ? branchSelect.value : '{{ secili_sube_id }}',
            year: {{ d_year }},
            month: {{ d_month }},"""

if broken_block in c:
    c = c.replace(broken_block, fixed_block)
    print("Fixed broken requestData block.")
else:
    # Simpler replacements for stray parts
    c = c.replace('year: {{ d_year }\n    }', 'year: {{ d_year }}')
    c = c.replace('month: { { d_month } }', 'month: {{ d_month }}')
    c = c.replace('year: {{ d_year } }', 'year: {{ d_year }}')

# 3. Handle parseFloat of labels that might have commas
c = c.replace('parseFloat(td.innerText)', 'parseFloat(unformatMoney(td.innerText))')
c = c.replace('parseFloat(efCol.innerText)', 'parseFloat(unformatMoney(efCol.innerText))')
c = c.replace('parseFloat(dgCol.innerText)', 'parseFloat(unformatMoney(dgCol.innerText))')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print("CalculateTotals output formatting and syntax cleanup finished.")
