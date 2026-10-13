/** Abridged life-table calculations and browser UI; no server or dependencies. */
export const SAMPLE = `age,mx,ax
0,0.005,0.1
1,0.0005,
5,0.0002,
15,0.0007,
25,0.001,
35,0.002,
45,0.004,
55,0.009,
65,0.02,
75,0.05,
85,0.12,`;

export function parseCSV(text) {
  const records = [];
  let fields = [], value = '', inQuotes = false;
  const pushRow = () => {
    fields.push(value.trim());
    if (fields.some(x => x !== '')) records.push(fields);
    fields = []; value = '';
  };
  const normalized = text.replace(/^\uFEFF/, '');
  for (let i = 0; i < normalized.length; i++) {
    const char = normalized[i];
    if (char === '"') {
      if (inQuotes && normalized[i + 1] === '"') { value += '"'; i++; }
      else { inQuotes = !inQuotes; }
    } else if (!inQuotes && char === ',') { fields.push(value.trim()); value = ''; }
    else if (!inQuotes && char === '\n') { pushRow(); }
    else if (char !== '\r' || inQuotes) { value += char; }
  }
  if (inQuotes) throw new Error('Unterminated quoted CSV field');
  if (fields.length || value) pushRow();
  if (records.length < 2) throw new Error('CSV requires a header and at least one age interval');
  const headers = records.shift().map(v => v.toLowerCase());
  if (!headers.includes('age') || !headers.includes('mx')) throw new Error('CSV requires age,mx columns (optional ax)');
  if (headers.length !== new Set(headers).size) throw new Error('CSV headers must be unique');
  return records.map((record, index) => {
    if (record.length !== headers.length) throw new Error(`Row ${index + 2}: incorrect number of columns`);
    return Object.fromEntries(headers.map((header, j) => [header, record[j]]));
  });
}

function finite(value, description) {
  if (value === null || value === undefined || String(value).trim() === '')
    throw new Error(`${description} is required`);
  const result = Number(value);
  if (!Number.isFinite(result)) throw new Error(`${description} must be a finite number`);
  return result;
}

export function constructTable(intervals, radix = 100000) {
  radix = finite(radix, 'Radix');
  if (radix <= 0) throw new Error('Radix must be positive');
  if (!Array.isArray(intervals) || intervals.length === 0) throw new Error('At least one age interval is required');
  let previous = -1;
  const table = intervals.map((interval, i) => {
    const age = finite(interval.age, `Row ${i + 1}: age`);
    const mx = finite(interval.mx, `Row ${i + 1}: mx`);
    if (age < 0 || age <= previous) throw new Error('Ages must be nonnegative and strictly increasing');
    if (mx < 0) throw new Error(`Row ${i + 1}: mx must be nonnegative`);
    previous = age;
    const last = i === intervals.length - 1;
    if (last) {
      if (mx === 0) throw new Error('The open-ended last interval requires mx > 0');
      if (interval.ax !== undefined && String(interval.ax).trim() !== '') throw new Error('ax is not used for the final open-ended interval');
      return { age, width: null, mx, ax: null, qx: 1 };
    }
    const width = finite(intervals[i + 1].age, `Row ${i + 2}: age`) - age;
    if (width <= 0) throw new Error('Ages must be strictly increasing');
    const ax = interval.ax === undefined || interval.ax === null || String(interval.ax).trim() === ''
      ? width / 2 : finite(interval.ax, `Row ${i + 1}: ax`);
    if (ax < 0 || ax > width) throw new Error(`Row ${i + 1}: ax must be between 0 and ${width}`);
    const denominator = mx === 0 ? null : 1 / mx + width - ax;
    const qx = mx === 0 ? 0 : denominator === 0 ? 1 : Math.min(1, width / denominator);
    return { age, width, mx, ax, qx };
  });
  let survivors = radix;
  for (const r of table) {
    r.lx = survivors;
    r.dx = survivors * r.qx;
    const next = Math.max(0, survivors - r.dx);
    r.Lx = r.width === null ? survivors / r.mx : r.width * next + r.ax * r.dx;
    if (!Number.isFinite(r.Lx)) throw new Error('Inputs produce non-finite person-years');
    survivors = next;
  }
  let T = 0;
  for (let i = table.length - 1; i >= 0; i--) {
    const r = table[i];
    T += r.Lx;
    r.Tx = T;
    r.ex = r.lx > 0 ? T / r.lx : null;
  }
  return table;
}

const columns = ['age', 'width', 'mx', 'ax', 'qx', 'lx', 'dx', 'Lx', 'Tx', 'ex'];
const format = (number, decimals = 3) => number === null ? '—' : Number(number).toLocaleString('en-US', { maximumFractionDigits: decimals });

export function toCSV(rows) {
  return [columns.join(','), ...rows.map(row => columns.map(k => row[k] === null ? '' : Number(row[k]).toPrecision(12)).join(','))].join('\r\n') + '\r\n';
}

function drawChart(root, table, radix) {
  const ns = 'http://www.w3.org/2000/svg';
  const make = (name, attrs = {}, text = null) => {
    const node = document.createElementNS(ns, name);
    Object.entries(attrs).forEach(([key, val]) => node.setAttribute(key, val));
    if (text !== null) node.textContent = text;
    root.append(node);
    return node;
  };
  root.replaceChildren();
  const left = 52, right = 765, top = 24, bottom = 240;
  const first = table[0].age, last = table[table.length - 1].age;
  const range = Math.max(1, last - first);
  const x = age => left + (age - first) / range * (right - left);
  const y = lx => bottom - lx / radix * (bottom - top);
  for (const share of [0, 0.25, 0.5, 0.75, 1]) {
    const py = y(radix * share);
    make('line', { x1: left, y1: py, x2: right, y2: py, stroke: '#2d4057', 'stroke-width': 1 });
    make('text', { x: left - 10, y: py + 4, fill: '#a9bfd0', 'text-anchor': 'end', 'font-size': 12 }, `${Math.round(share * 100)}%`);
  }
  make('polyline', {
    points: table.map(row => `${x(row.age)},${y(row.lx)}`).join(' '),
    fill: 'none', stroke: '#55d6c2', 'stroke-width': 3, 'stroke-linejoin': 'round'
  });
  for (const row of table) make('circle', { cx: x(row.age), cy: y(row.lx), r: 4, fill: '#55d6c2' });
  make('text', { x: left, y: bottom + 23, fill: '#a9bfd0', 'font-size': 12 }, `${first} years`);
  make('text', { x: right, y: bottom + 23, fill: '#a9bfd0', 'text-anchor': 'end', 'font-size': 12 }, `${last}+ years`);
}

export function initApp(doc = document) {
  const input = doc.getElementById('csv-input');
  const file = doc.getElementById('csv-file');
  const radixInput = doc.getElementById('radix');
  const error = doc.getElementById('error');
  const tableBody = doc.getElementById('results-body');
  const summary = doc.getElementById('summary');
  const chart = doc.getElementById('survival-chart');
  const download = doc.getElementById('download');
  let latest = null;

  doc.getElementById('calculate').addEventListener('click', () => {
    error.textContent = '';
    latest = null;
    download.disabled = true;
    tableBody.replaceChildren();
    chart.replaceChildren();
    summary.textContent = 'No results';
    try {
      const radix = finite(radixInput.value, 'Radix');
      latest = constructTable(parseCSV(input.value), radix);
      const first = latest[0];
      summary.textContent = `Life expectancy at age ${format(first.age)}: ${format(first.ex, 2)} years · ${latest.length} age groups · Radix ${format(radix, 0)}`;
      for (const row of latest) {
        const tr = doc.createElement('tr');
        for (const key of columns) {
          const td = doc.createElement('td');
          td.textContent = format(row[key], ['qx', 'mx'].includes(key) ? 6 : 2);
          tr.append(td);
        }
        tableBody.append(tr);
      }
      drawChart(chart, latest, radix);
      download.disabled = false;
    } catch (exc) { error.textContent = exc.message; }
  });

  doc.getElementById('sample').addEventListener('click', () => {
    input.value = SAMPLE;
    doc.getElementById('calculate').click();
  });
  file.addEventListener('change', async () => {
    const uploaded = file.files?.[0];
    if (!uploaded) return;
    error.textContent = '';
    try {
      if (uploaded.size > 1_000_000) throw new Error('CSV must be 1 MB or smaller');
      input.value = await uploaded.text();
      doc.getElementById('calculate').click();
    } catch (exc) { error.textContent = exc.message; }
    finally { file.value = ''; }
  });
  download.addEventListener('click', () => {
    if (!latest) return;
    const url = URL.createObjectURL(new Blob([toCSV(latest)], { type: 'text/csv;charset=utf-8' }));
    const anchor = doc.createElement('a');
    anchor.href = url; anchor.download = 'life-table.csv';
    doc.body.append(anchor); anchor.click(); anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  });
  doc.getElementById('calculate').click();
}

if (typeof document !== 'undefined' && document.getElementById('calculate')) initApp();
