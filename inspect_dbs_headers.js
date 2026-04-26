const XLSX = require('xlsx');

function dump(file) {
    console.log(`--- Headers for ${file} ---`);
    try {
        const workbook = XLSX.readFile(file);
        const sheet = workbook.Sheets[workbook.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json(sheet, { header: 1 });
        
        // Print rows 10 to 18
        rows.slice(10, 18).forEach((row, i) => {
            const rowStr = row.map((cell, j) => cell ? `[C${j}: ${cell}]` : `[C${j}: -]`).join(' ');
            console.log(`Row ${i+10}: ${rowStr}`);
        });
    } catch (e) {
        console.error(`Error reading ${file}: ${e.message}`);
    }
}

dump('c:\\projects\\SilverCloud\\DBSHamData.xls');
