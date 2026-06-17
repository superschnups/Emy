const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3002;

const LOCAL_MAC_FILE = '/Users/jessi/Library/Application Support/com.jessi.precision_engine/shortcuts.json';
const BACKUP_FILE = path.join(__dirname, 'data/shortcuts.json');

// Helper to determine active file
const getShortcutsFile = () => {
  if (fs.existsSync(LOCAL_MAC_FILE)) {
    return LOCAL_MAC_FILE;
  }
  return BACKUP_FILE;
};

// JSON parser middleware
app.use(express.json());

// Basic Auth Middleware (User: admin / Pass: emy2026)
const authMiddleware = (req, res, next) => {
  const authHeader = req.headers.authorization;
  if (!authHeader) {
    res.setHeader('WWW-Authenticate', 'Basic realm="Shortcuts Dashboard"');
    return res.status(401).send('Authentication required');
  }
  
  try {
    const token = authHeader.split(' ')[1];
    const credentials = Buffer.from(token, 'base64').toString('utf8').split(':');
    const user = credentials[0];
    const pass = credentials[1];
    
    if (user === 'admin' && pass === 'emy2026') {
      return next();
    }
  } catch (err) {
    console.error('Auth parse error:', err);
  }
  
  res.setHeader('WWW-Authenticate', 'Basic realm="Shortcuts Dashboard"');
  return res.status(401).send('Authentication required');
};

app.use(authMiddleware);

// Serve static assets from the current directory
app.use(express.static(__dirname));

// Endpoints
app.get('/api/shortcuts', (req, res) => {
  try {
    const file = getShortcutsFile();
    if (!fs.existsSync(file)) {
      return res.json({});
    }
    const data = JSON.parse(fs.readFileSync(file, 'utf8'));
    res.json(data);
  } catch (e) {
    console.error('Error reading shortcuts:', e);
    res.status(500).json({ ok: false, error: e.message });
  }
});

app.post('/api/shortcuts', (req, res) => {
  try {
    const file = getShortcutsFile();
    
    // Ensure parent dir exists
    const dir = path.dirname(file);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    if (file === LOCAL_MAC_FILE) {
      const payload = req.body;
      let flatArray = [];
      
      // If it's already an array, save directly
      if (Array.isArray(payload)) {
        flatArray = payload;
      } else {
        // Convert Format B (Dict) back to Format A (Tauri Array)
        Object.keys(payload).forEach(app => {
          (payload[app] || []).forEach(s => {
            flatArray.push({
              id: s.id || String(Date.now() + Math.floor(Math.random() * 1000)),
              application: app,
              command_name: s.name,
              keys: (s.key || '').split('+').map(k => k.trim()).filter(Boolean),
              context: s.tags && s.tags[0] ? s.tags[0] : 'Global',
              created_with: s.tags && s.tags[1] ? s.tags[1] : 'Web Dashboard',
              app_icon: s.app_icon || 'bolt',
              app_color: s.app_color || '#ffb59d'
            });
          });
        });
      }
      fs.writeFileSync(file, JSON.stringify(flatArray, null, 2), 'utf8');
    } else {
      // Backup file Format B (Dict)
      fs.writeFileSync(file, JSON.stringify(req.body, null, 2), 'utf8');
    }
    
    res.json({ ok: true });
  } catch (e) {
    console.error('Error saving shortcuts:', e);
    res.status(500).json({ ok: false, error: e.message });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`=========================================`);
  console.log(`  Shortcuts Dashboard Server started!    `);
  console.log(`  Local:   http://localhost:${PORT}      `);
  console.log(`  File:    ${getShortcutsFile()}         `);
  console.log(`  Credentials: admin / emy2026           `);
  console.log(`=========================================`);
});
