import initSqlJs from 'sql.js/dist/sql-wasm.js';

let dbInstance = null;

export const initDb = async () => {
  if (dbInstance) return true;
  
  try {
    const SQL = await initSqlJs({
       locateFile: file => `/${file}`
    });
    
    const dbFile = await fetch('/super_lig.db');
    const buf = await dbFile.arrayBuffer();
    
    dbInstance = new SQL.Database(new Uint8Array(buf));
    return true;
  } catch (err) {
    console.error("Failed to init database", err);
    return false;
  }
};

export const runQuery = (sql, params = []) => {
  if (!dbInstance) {
    console.warn("DB not initialized yet");
    return [];
  }
  
  try {
    const res = dbInstance.exec(sql, params);
    if (res.length === 0) return [];
    
    // sql.js returns [{ columns: [...], values: [ [...] ] }]
    // we want to map this to an array of objects
    const columns = res[0].columns;
    const values = res[0].values;
    
    return values.map(row => {
      let obj = {};
      columns.forEach((col, idx) => {
        obj[col] = row[idx];
      });
      return obj;
    });
  } catch(e) {
    console.error("Query failed:", e);
    return [];
  }
};
