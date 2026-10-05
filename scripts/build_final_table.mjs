// Requested CSV only: author typed values with Artifact Tool, then serialize its
// verified range. No extra XLSX is produced. Run from the repository root.
import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook } from '@oai/artifact-tool';

const root = process.cwd();
const records = JSON.parse(await fs.readFile(path.join(root, 'research_outputs/phase5/central_results.json'), 'utf8'));
const headers = Object.keys(records[0]);
const values = [headers, ...records.map(row => headers.map(key => row[key]))];
const wb = Workbook.create();
const sheet = wb.worksheets.add('Final results');
const range = sheet.getRange(`A1:I${values.length}`);
range.values = values;
range.format.font = { name: 'Arial', size: 10 };
range.format.rowHeight = 32;
range.format.verticalAlignment = 'center';
sheet.showGridLines = false;
sheet.getRange('A1:I1').format.fill = '#203348';
sheet.getRange('A1:I1').format.font = { name: 'Arial', size: 10, color: '#FFFFFF', bold: true };
sheet.getRange('A1:I1').format.wrapText = true;
sheet.getRange('A1:I1').format.rowHeight = 44;
sheet.getRange('A1:A7').format.columnWidth = 36;
sheet.getRange('B1:B7').format.columnWidth = 30;
sheet.getRange('C1:H7').format.columnWidth = 19;
sheet.getRange('I1:I7').format.columnWidth = 43;
sheet.getRange('C2:H7').setNumberFormat('0.0000');
wb.recalculate();
const check = await wb.inspect({ kind: 'table', range: 'Final results!A1:I7', include: 'values,formulas', tableMaxRows: 7, tableMaxCols: 9, maxChars: 4000 });
await fs.writeFile(path.join(root, 'research_outputs/phase5/table_inspection.ndjson'), check.ndjson);
const exported = range.values;
for (let r = 0; r < values.length; r++) for (let c = 0; c < headers.length; c++) {
  if ((exported[r][c] ?? null) !== values[r][c]) throw new Error(`Cell changed: ${r},${c}`);
}
const quote = value => value == null ? '' : /[",\r\n]/.test(String(value)) ? `"${String(value).replaceAll('"', '""')}"` : String(value);
const csv = exported.map(row => row.map(quote).join(',')).join('\n') + '\n';
await fs.writeFile(path.join(root, 'research_outputs/tables/final_results.csv'), csv);
const preview = await wb.render({ sheetName: 'Final results', range: 'A1:I7', scale: 1, format: 'png' });
await fs.writeFile(path.join(root, 'research_outputs/phase5/final_table_preview.png'), new Uint8Array(await preview.arrayBuffer()));
const number = value => value == null ? 'N/A' : typeof value === 'number' ? value.toFixed(4) : String(value);
const mdHeaders = headers.slice(1);
const md = '# Final core results\n\n' + '| ' + mdHeaders.join(' | ') + ' |\n| ' + mdHeaders.map(() => '---').join(' | ') + ' |\n' + exported.slice(1).map(row => '| ' + row.slice(1).map(number).join(' | ') + ' |').join('\n') + '\n\nValues come from frozen Phase 4 results, calibration and robustness outputs. N/A (blank CSV field) means unavailable or unmeasured, never zero. ECE is uncalibrated top-label ECE with 15 bins. Robustness is the worst delta in Macro F1 over 12 registered perturbations, measured only for the diagnostic weighted CNN. Table order is fixed and is not a Test-based ranking. NDCI is the validation-selected model, despite zero validation High F1. No CNN passed the class guard. LR is a comparator, not a post-hoc selection. Full experiment IDs remain in the CSV.\n\nSources: [results](../phase4/results.json), [selection](../phase4/selection.json), [calibration](../phase4/calibration.json), [robustness](../phase4/robustness_metrics.csv).\n';
await fs.writeFile(path.join(root, 'research_outputs/tables/final_results.md'), md);
console.log('CSV and Markdown exported; 6 model rows verified without rounding the CSV.');
