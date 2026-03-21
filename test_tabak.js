const XLSX = require('xlsx');

const filePath = 'C:\\Users\\sg.msa\\Downloads\\Şube Bazlı Toplam Tabak Sayısı - 1.02.2026 06_00_00 - 1.03.2026 06_00_00.xlsx';

try {
    const workbook = XLSX.readFile(filePath);
    console.log('Sheet names:', workbook.SheetNames);

    for (const name of workbook.SheetNames) {
        const ws = workbook.Sheets[name];
        console.log(`\n--- Sheet: "${name}" ---`);

        // Try default parse
        const rows = XLSX.utils.sheet_to_json(ws, { defval: "" });
        console.log(`  sheet_to_json rows: ${rows.length}`);
        if (rows.length > 0) {
            console.log('  First row keys:', Object.keys(rows[0]));
            console.log('  First row:', JSON.stringify(rows[0]));
        }

        // Try raw parse with header:1 to get array of arrays
        const rawRows = XLSX.utils.sheet_to_json(ws, { header: 1 });
        console.log(`  raw array rows: ${rawRows.length}`);
        if (rawRows.length > 0) {
            console.log('  Raw row 0:', JSON.stringify(rawRows[0]));
        }
        if (rawRows.length > 1) {
            console.log('  Raw row 1:', JSON.stringify(rawRows[1]));
        }
        if (rawRows.length > 2) {
            console.log('  Raw row 2:', JSON.stringify(rawRows[2]));
        }
    }
} catch (e) {
    console.error('Error:', e.message);
}
