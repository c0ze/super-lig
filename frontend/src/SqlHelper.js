import initSqlJs from 'sql.js/dist/sql-wasm.js';

const BASE_URL = import.meta.env?.BASE_URL ?? '/';

const resolveAsset = (file) => {
  const base = BASE_URL.endsWith('/') ? BASE_URL : `${BASE_URL}/`;
  return `${base}${file}`;
};

let dbInstance = null;

export const initDb = async () => {
  if (dbInstance) return true;

  try {
    const SQL = await initSqlJs({
      locateFile: (file) => resolveAsset(file),
    });

    const dbFile = await fetch(resolveAsset('site.db.gzip'));
    if (!dbFile.ok) {
      throw new Error(`Failed to fetch site.db.gzip: ${dbFile.status}`);
    }
    if (typeof DecompressionStream === 'undefined') {
      throw new Error('Browser does not support DecompressionStream');
    }
    const decompressed = dbFile.body.pipeThrough(new DecompressionStream('gzip'));
    const buf = await new Response(decompressed).arrayBuffer();

    dbInstance = new SQL.Database(new Uint8Array(buf));
    return true;
  } catch (err) {
    console.error('Failed to init database', err);
    return false;
  }
};

export const runQuery = (sql, params = []) => {
  if (!dbInstance) {
    console.warn('DB not initialized yet');
    return [];
  }

  try {
    const res = dbInstance.exec(sql, params);
    if (res.length === 0) return [];

    const { columns, values } = res[0];
    return values.map((row) => {
      const obj = {};
      columns.forEach((col, idx) => {
        obj[col] = row[idx];
      });
      return obj;
    });
  } catch (e) {
    console.error('Query failed:', e);
    return [];
  }
};
