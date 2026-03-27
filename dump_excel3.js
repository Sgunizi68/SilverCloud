const XLSX = require('xlsx');
const fs = require('fs');
const path = 'C:\\Users\\sg.msa\\Downloads\\Satış Tipi - Ödeme Tipi Özet - 1.01.2026 06_00_00 - 1.01.2027 06_00_00.xlsx';
try {
    const wb = XLSX.readFile(path);
    const worksheet = wb.Sheets[wb.SheetNames[0]];

    let range = { s: {c:10000000, r:10000000}, e: {c:0, r:0} };
    for (const key in worksheet) {
        if (key[0] === '!') continue;
        const cell = XLSX.utils.decode_cell(key);
        if (range.s.c > cell.c) range.s.c = cell.c;
        if (range.s.r > cell.r) range.s.r = cell.r;
        if (range.e.c < cell.c) range.e.c = cell.c;
        if (range.e.r < cell.r) range.e.r = cell.r;
    }
    if (range.s.c <= range.e.c && range.s.r <= range.e.r) {
        worksheet['!ref'] = XLSX.utils.encode_range(range);
    }

    const js = XLSX.utils.sheet_to_json(worksheet);
    fs.writeFileSync('excel_debug3.txt', 'Rows found after fix: ' + js.length + '\nSample: ' + JSON.stringify(js[0]));
} catch (e) {
    fs.writeFileSync('excel_debug3.txt', 'Error: ' + e.toString());
}
