const XLSX = require('xlsx');

const filePath = "C:\\Users\\sg.msa\\OneDrive - ÇELEBİ AVIATION\\Personel\\Programming\\Yüklemeler\\Archieve\\Şube Bazlı Toplam Tabak Sayısı - 1.03.2026 06_00_00 - 23.03.2026 06_00_00.xlsx";
const workbook = XLSX.readFile(filePath, { cellDates: true });
const ws = workbook.Sheets[workbook.SheetNames[0]];

console.log("Original !ref:", ws['!ref']);

// Find the true boundaries manually
let maxR = 0;
let maxC = 0;
for (let key in ws) {
    if (key[0] === '!') continue;
    const cellRef = XLSX.utils.decode_cell(key);
    if (cellRef.r > maxR) maxR = cellRef.r;
    if (cellRef.c > maxC) maxC = cellRef.c;
}

console.log(`Actual max Row: ${maxR}, max Col: ${maxC}`);

// Recalculate ref and output again
ws['!ref'] = XLSX.utils.encode_range({s:{r:0,c:0}, e:{r:maxR, c:maxC}});
const rawRows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: "" });
console.log(`Rows after fixing !ref: ${rawRows.length}`);

if (rawRows.length > 1) {
    console.log("Row 1:", rawRows[1]);
}
