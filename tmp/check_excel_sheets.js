const XLSX = require('xlsx');
const fs = require('fs');

const filePath = "C:\\Users\\sg.msa\\OneDrive - ÇELEBİ AVIATION\\Personel\\Programming\\Yüklemeler\\Archieve\\Şube Bazlı Toplam Tabak Sayısı - 1.03.2026 06_00_00 - 23.03.2026 06_00_00.xlsx";
const workbook = XLSX.readFile(filePath, { cellDates: true });

const out = {};
for (let name of workbook.SheetNames) {
    const ws = workbook.Sheets[name];
    const rawRows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: "" });
    out[name] = rawRows.slice(0, 15);
}

fs.writeFileSync('C:\\projects\\SilverCloud\\tmp\\excel_dump2.json', JSON.stringify(out, null, 2), 'utf8');
