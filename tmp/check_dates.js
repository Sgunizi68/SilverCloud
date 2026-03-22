const XLSX = require('xlsx');

const filePath = "C:\\Users\\sg.msa\\OneDrive - ÇELEBİ AVIATION\\Personel\\Programming\\Yüklemeler\\Archieve\\Şube Bazlı Toplam Tabak Sayısı - 1.03.2026 06_00_00 - 23.03.2026 06_00_00.xlsx";
const workbook = XLSX.readFile(filePath);
const ws = workbook.Sheets[workbook.SheetNames[0]];

let maxR = 0, maxC = 0;
for (let key in ws) {
    if (key[0] === '!') continue;
    const cellRef = XLSX.utils.decode_cell(key);
    if (cellRef.r > maxR) maxR = cellRef.r;
    if (cellRef.c > maxC) maxC = cellRef.c;
}
ws['!ref'] = XLSX.utils.encode_range({s:{r:0,c:0}, e:{r:maxR, c:maxC}});

const rawRows = XLSX.utils.sheet_to_json(ws, { header: 1, raw: false, defval: "" });

console.log("Row 1 date:", rawRows[1][1]);
