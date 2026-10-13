import test from 'node:test';
import assert from 'node:assert/strict';
import {constructTable, parseCSV, toCSV, SAMPLE} from './app.js';

test('deterministic constant mortality table and radix conservation', () => {
  const t = constructTable(parseCSV('age,mx\n0,0.02\n5,0.02'));
  assert.ok(Math.abs(t[0].ex - 50) < 1e-10);
  assert.ok(Math.abs(t.reduce((sum, r) => sum + r.dx, 0) - 100000) < 1e-7);
  assert.equal(t[1].width, null);
  assert.equal(t[1].qx, 1);
});
test('sample table is finite and outputs CSV', () => {
  const t = constructTable(parseCSV(SAMPLE));
  assert.equal(t.length, 11);
  assert.ok(t.every(r => Number.isFinite(r.Lx) && Number.isFinite(r.Tx)));
  assert.ok(toCSV(t).includes('age,width,mx,ax,qx,lx,dx,Lx,Tx,ex'));
});
test('ax changes survivorship and expectancy', () => {
  const a = constructTable(parseCSV('age,mx,ax\n0,0.1,0.1\n1,0.01,'));
  const b = constructTable(parseCSV('age,mx,ax\n0,0.1,\n1,0.01,'));
  assert.notEqual(a[0].ex, b[0].ex);
});
test('reject malformed and invalid inputs', () => {
  for (const s of ['age,mx\n0,0', 'age,mx\n0,0.1\n0,0.2', 'age,mx\n0,NaN\n1,0.1', 'age,mx,ax\n0,0.1,2\n1,0.1,', 'age,mx\n0,0.1\n1,-0.1', 'age,mx\n0,0.1\n1,0.1,2']) {
    assert.throws(() => constructTable(parseCSV(s)));
  }
  assert.throws(() => parseCSV('age,mx\n"0,0.1'));
});
test('CSV reader accepts BOM, CRLF and quoted columns', () => {
  assert.deepEqual(parseCSV('\ufeffage,mx\r\n"0","0.02"\r\n"5","0.02"\r\n'), [{age:'0',mx:'0.02'}, {age:'5',mx:'0.02'}]);
});
