const XLSX = require('xlsx');
const fs = require('fs');
const path = 'C:\\Users\\sg.msa\\Downloads\\Satış Tipi - Ödeme Tipi Özet - 1.01.2026 06_00_00 - 1.01.2027 06_00_00.xlsx';
try {
    const wb = XLSX.readFile(path);
    const sheet = wb.Sheets[wb.SheetNames[0]];
    const ref = sheet['!ref'];
    fs.writeFileSync('excel_debug2.txt', 'Ref property: ' + String(ref) + '\nKeys: ' + JSON.stringify(Object.keys(sheet).slice(0, 20)));
} catch (e) {
    fs.writeFileSync('excel_debug2.txt', 'Error: ' + e.toString());
}
