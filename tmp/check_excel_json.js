const XLSX = require('xlsx');
const fs = require('fs');

const filePath = "C:\\Users\\sg.msa\\OneDrive - ÇELEBİ AVIATION\\Personel\\Programming\\Yüklemeler\\Archieve\\Şube Bazlı Toplam Tabak Sayısı - 1.03.2026 06_00_00 - 23.03.2026 06_00_00.xlsx";
const workbook = XLSX.readFile(filePath, { cellDates: true });
const ws = workbook.Sheets[workbook.SheetNames[0]];
const rawRows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: "" });

const out = [];
for (let i = 0; i < Math.min(rawRows.length, 15); i++) {
    out.push(rawRows[i]);
}

fs.writeFileSync('C:\\projects\\SilverCloud\\tmp\\excel_dump.json', JSON.stringify(out, null, 2), 'utf8');
