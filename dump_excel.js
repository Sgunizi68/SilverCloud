const XLSX = require('xlsx');
const fs = require('fs');
const path = 'C:\\Users\\sg.msa\\Downloads\\Satış Tipi - Ödeme Tipi Özet - 1.01.2026 06_00_00 - 1.01.2027 06_00_00.xlsx';
try {
    const wb = XLSX.readFile(path);
    const sheets = wb.SheetNames;
    let output = "Sheets: " + JSON.stringify(sheets) + "\n";
    for(let s of sheets) {
        const js = XLSX.utils.sheet_to_json(wb.Sheets[s]);
        output += "Sheet " + s + " Length: " + js.length + "\n";
        if(js.length > 0) {
            output += "Row 0: " + JSON.stringify(js[0], null, 2) + "\n";
        }
    }
    fs.writeFileSync('excel_debug.txt', output);
} catch (e) {
    fs.writeFileSync('excel_debug.txt', 'Error: ' + e.toString());
}
