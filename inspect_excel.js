const XLSX = require('xlsx');

function dump(file) {
    console.log(`--- Headers for ${file} ---`);
    const workbook = XLSX.readFile(file);
    const sheet = workbook.Sheets[workbook.SheetNames[0]];
    const rows = XLSX.utils.sheet_to_json(sheet, { header: 1 });
    
    // Print first 10 rows to see structure
    rows.slice(0, 10).forEach((row, i) => {
        const rowStr = row.map((cell, j) => cell ? `[C${j}: ${cell}]` : `[C${j}: -]`).join(' ');
        console.log(`Row ${i}: ${rowStr}`);
    });
}

dump('POSHamData.xls');
dump('POSUpdateData.xlsx');
