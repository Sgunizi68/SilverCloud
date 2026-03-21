import os
import re

path = r'c:\projects\SilverCloud\app\templates\gelir_girisi.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add JS helper functions before calculateTotals
js_helpers = """
    function formatMoney(n) {
        if (n === null || n === undefined || isNaN(n) || n === '') return '';
        let num = parseFloat(n);
        if (isNaN(num)) return '';
        return num.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    }

    function unformatMoney(s) {
        if (!s || typeof s !== 'string') return s;
        return s.replace(/,/g, '');
    }

    function onInputFocus(el) {
        let val = unformatMoney(el.value);
        if (val === '') return;
        let num = parseFloat(val);
        el.value = isNaN(num) ? '' : num.toFixed(2);
    }

    function onInputBlur(el) {
        let val = el.value.trim();
        if (val === '') {
            el.value = '';
            return;
        }
        let num = parseFloat(val);
        el.value = isNaN(num) ? '' : formatMoney(num);
    }
"""

# Inject helpers at the start of scripts
c = c.replace('function calculateTotals() {', js_helpers + '\n    function calculateTotals() {')

# 2. Update calculateTotals to use unformatMoney
# Change parseFloat(inp.value) and parseFloat(inputElement.value)
c = c.replace('parseFloat(inp.value)', 'parseFloat(unformatMoney(inp.value))')
c = c.replace('parseFloat(inputElement.value)', 'parseFloat(unformatMoney(inputElement.value))')

# 3. Update HTML inputs to type="text" and add focus/blur events
# Replace current number inputs patterns
# Pattern: <input type="number" step="0.01" class="cell-input ... value="{{ ... }}" onblur="saveCell(this)" onchange="calculateTotals()" ...>

def replace_inputs(match):
    content = match.group(0)
    # Change type
    content = content.replace('type="number"', 'type="text"')
    # Remove step
    content = content.replace('step="0.01"', '')
    # Wrap value with formatMoney if it's dynamic
    # Actually value is already formatted via Jinja, but we might want to re-format it via JS on load or Jinja
    # Current value: value="{{ '%.2f' | format(r_val) if r_val else '' }}"
    
    # Add focus/blur events
    if 'onfocus' not in content:
        content = content.replace('onblur="saveCell(this)"', 'onfocus="onInputFocus(this)" onblur="onInputBlur(this); saveCell(this)"')
    
    return content

# Regex for the inputs
c = re.sub(r'<input[^>]+cell-input[^>]+>', replace_inputs, c)

# 4. Final fix for any stray Jinja errors that might have been reintroduced
c = c.replace('year: {{ d_year } }', 'year: {{ d_year }}')
c = c.replace('month: {{ d_month } }', 'month: {{ d_month }}')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print("Formatting and input type conversion completed.")
