const express = require('express');
const multer = require('multer');
const sharp = require('sharp');
const path = require('path');
const fs = require('fs');
const { exec } = require('child_process');
const os = require('os');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3001;
app.set('trust proxy', true);

// CORS für den öffentlichen Gästebuch-Endpunkt
app.use(cors({
  origin: function(origin, callback) {
    callback(null, true);
  },
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// --- BASIC AUTH CONFIG ---
const ADMIN_USER = 'admin';
const ADMIN_PASS = 'bonzei'; // Empfehlung: Ändern!

const IMAGES_DIR = path.join(__dirname, 'static/gallery/images');
const HERO_DIR = path.join(__dirname, 'static/hero');
const UEBERMICH_IMG_DIR = path.join(__dirname, 'static/uebermich');
const DATA_FILE = path.join(__dirname, 'data/gallery.json');
const HOMEPAGE_FILE = path.join(__dirname, 'data/homepage.json');
const CATEGORIES_FILE = path.join(__dirname, 'data/categories.json');
const UEBERMICH_FILE = path.join(__dirname, 'data/uebermich.json');
const ERFOLGE_FILE = path.join(__dirname, 'data/erfolge.json');
const ERFOLGE_IMG_DIR = path.join(__dirname, 'static/erfolge-img');
const GALERIE_PAGE_FILE = path.join(__dirname, 'data/galerie.json');
const GAESTEBUCH_FILE = path.join(__dirname, 'data/gaestebuch.json');
const GLOBAL_FILE = path.join(__dirname, 'data/global.json');
const GAESTEBUCH_IMG_DIR = path.join(__dirname, 'static/gaestebuch-img');
const DYNAMIC_DATA_DIR = path.join(__dirname, 'data_dynamic');
const ERFOLGE_INTERACTIONS_FILE = path.join(DYNAMIC_DATA_DIR, 'erfolge_interactions.json');

if (!fs.existsSync(DYNAMIC_DATA_DIR)) fs.mkdirSync(DYNAMIC_DATA_DIR, { recursive: true });
if (!fs.existsSync(UEBERMICH_IMG_DIR)) fs.mkdirSync(UEBERMICH_IMG_DIR, { recursive: true });
if (!fs.existsSync(HERO_DIR)) fs.mkdirSync(HERO_DIR, { recursive: true });
if (!fs.existsSync(ERFOLGE_IMG_DIR)) fs.mkdirSync(ERFOLGE_IMG_DIR, { recursive: true });
if (!fs.existsSync(GAESTEBUCH_IMG_DIR)) fs.mkdirSync(GAESTEBUCH_IMG_DIR, { recursive: true });


// Basic Auth Middleware
app.use((req, res, next) => {
  
  // Öffentliche Pfade definieren
  const publicPaths = [
    '/api/gaestebuch/public',
    '/api/erfolge-interactions', // GET und POST für Likes/Kommentare
    '/images/',
    '/hero/',
    '/uebermich-img/',
    '/erfolge-img/',
    '/gaestebuch-img/'
  ];

  // Wenn es ein öffentlicher Pfad ist UND (es ist GET/POST ODER es ist nicht der Admin-Endpunkt)
  // Speziell für Erfolge-Interaktionen: GET (laden) und POST (like/kommentar) sind frei.
  // PUT (editieren) und DELETE (löschen) erfordern Login.
  if (req.path.startsWith('/api/erfolge-interactions')) {
    if (req.method === 'GET' || req.method === 'POST') {
      return next();
    }
  }

  if (publicPaths.some(p => req.path.startsWith(p) && p !== '/api/erfolge-interactions')) {
    return next();
  }

  const auth = { login: ADMIN_USER, password: ADMIN_PASS };
  const b64auth = (req.headers.authorization || '').split(' ')[1] || '';
  if (!b64auth) {
    if (!req.xhr && !req.headers.accept.includes('json')) res.set('WWW-Authenticate', 'Basic realm="MiyaKarate Admin"');
    return res.status(401).send('Authentication required.');
  }

  const [login, password] = Buffer.from(b64auth, 'base64').toString().split(':');

  if (login === auth.login && password === auth.password) {
    return next();
  }

  if (!req.xhr && !req.headers.accept.includes('json')) res.set('WWW-Authenticate', 'Basic realm="MiyaKarate Admin"');
  res.status(401).send('Authentication required.');
});

app.use(express.json());
app.use('/images', express.static(IMAGES_DIR));

// Multer: temporärer Speicher, dann sharp übernimmt
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 100 * 1024 * 1024 }, // 100MB limit für Videos
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/') || file.mimetype.startsWith('video/')) cb(null, true);
    else cb(new Error('Nur Bilder und Videos erlaubt!'));
  }
});

function readGallery() {
  return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
}
function writeGallery(data) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
}

// Upload
app.post('/api/upload', upload.array('photos', 20), async (req, res) => {
  try {
    const gallery = readGallery();
    const added = [];

    for (const file of req.files) {
      const id = Date.now() + '-' + Math.random().toString(36).slice(2, 7);
      const filename = id + '.webp';
      const thumbname = id + '-thumb.webp';

      // Vollbild (max 1200px)
      await sharp(file.buffer)
        .resize(1200, 1200, { fit: 'inside', withoutEnlargement: true })
        .webp({ quality: 85 })
        .toFile(path.join(IMAGES_DIR, filename));

      // Thumbnail (400px)
      await sharp(file.buffer)
        .resize(400, 400, { fit: 'cover' })
        .webp({ quality: 80 })
        .toFile(path.join(IMAGES_DIR, thumbname));

      const photo = {
        id,
        filename,
        thumb: thumbname,
        title: req.body.title || file.originalname.replace(/\.[^.]+$/, ''),
        kategorie: req.body.kategorie || 'Training',
        datum: new Date().toISOString().slice(0, 10)
      };
      gallery.photos.unshift(photo);
      added.push(photo);
    }

    writeGallery(gallery);
    res.json({ ok: true, added });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// Foto-Metadaten updaten
app.put('/api/photo/:id', (req, res) => {
  const gallery = readGallery();
  const photo = gallery.photos.find(p => p.id === req.params.id);
  if (!photo) return res.status(404).json({ ok: false });
  if (req.body.title !== undefined) photo.title = req.body.title;
  if (req.body.kategorie !== undefined) photo.kategorie = req.body.kategorie;
  writeGallery(gallery);
  res.json({ ok: true, photo });
});

// Foto löschen
app.delete('/api/photo/:id', (req, res) => {
  const gallery = readGallery();
  const idx = gallery.photos.findIndex(p => p.id === req.params.id);
  if (idx === -1) return res.status(404).json({ ok: false });
  const [photo] = gallery.photos.splice(idx, 1);
  [photo.filename, photo.thumb].forEach(f => {
    const fp = path.join(IMAGES_DIR, f);
    if (fs.existsSync(fp)) fs.unlinkSync(fp);
  });
  writeGallery(gallery);
  res.json({ ok: true });
});

// Alle Fotos
app.get('/api/photos', (req, res) => {
  res.json(readGallery());
});

// ── Kategorien API ────────────────────────────────────────────
function readCategories() {
  if (!fs.existsSync(CATEGORIES_FILE)) return ['Training', 'Wettkämpfe', 'Gürtelprüfungen'];
  return JSON.parse(fs.readFileSync(CATEGORIES_FILE, 'utf8'));
}
function writeCategories(cats) {
  fs.writeFileSync(CATEGORIES_FILE, JSON.stringify(cats, null, 2));
}

app.get('/api/categories', (req, res) => {
  res.json(readCategories());
});

app.post('/api/categories', (req, res) => {
  const name = (req.body.name || '').trim();
  if (!name) return res.status(400).json({ ok: false, error: 'Name fehlt' });
  const cats = readCategories();
  if (cats.includes(name)) return res.status(409).json({ ok: false, error: 'Existiert bereits' });
  cats.push(name);
  writeCategories(cats);
  res.json({ ok: true, categories: cats });
  rebuildAndDeploy();
});

app.delete('/api/categories/:name', (req, res) => {
  const cats = readCategories().filter(c => c !== req.params.name);
  writeCategories(cats);
  res.json({ ok: true, categories: cats });
  rebuildAndDeploy();
});

// ── Homepage API ──────────────────────────────────────────────
function readHomepage() {
  return JSON.parse(fs.readFileSync(HOMEPAGE_FILE, 'utf8'));
}
function writeHomepage(data) {
  fs.writeFileSync(HOMEPAGE_FILE, JSON.stringify(data, null, 2));
}

app.get('/api/homepage', (req, res) => {
  res.json(readHomepage());
});

function rebuildAndDeploy() {
  const isServer = os.platform() === 'linux';
  let cmd;

  if (isServer) {
    // Auf dem Server: Hugo bauen und lokal nach /var/www/ kopieren
    cmd = `cd ${__dirname} && /usr/local/bin/hugo --minify && cp -r public/* /var/www/emy-karate/ && cp -r public/* /var/www/emy.bonzeipunk.de/`;
  } else {
    // Lokal: Hugo bauen und per SSH/Rsync auf Server schieben
    const SSH_KEY = '/Users/jessi/.ssh/vpsserver/vpsserver';
    cmd = `cd ${__dirname} && hugo --minify && SSH_ASKPASS_REQUIRE=never ssh-add ${SSH_KEY} <<< "bonzeikiller" 2>/dev/null; rsync -az --delete -e "ssh -o StrictHostKeyChecking=no -i ${SSH_KEY}" ${__dirname}/public/ root@217.160.212.198:/var/www/emy-karate/ && rsync -az --delete -e "ssh -o StrictHostKeyChecking=no -i ${SSH_KEY}" ${__dirname}/public/ root@217.160.212.198:/var/www/emy.bonzeipunk.de/`;
  }

  console.log('Starte Rebuild/Deploy...');
  exec(cmd, { shell: '/bin/bash' }, (err, stdout, stderr) => {
    if (err) {
      console.error('Deploy-Fehler:', err.message);
      console.error('Stderr:', stderr);
    } else {
      console.log('✓ Deploy erfolgreich');
      if (stdout) console.log('Stdout:', stdout);
    }
  });
}

app.put('/api/homepage', (req, res) => {
  const hp = readHomepage();
  if (req.body.siteTitle !== undefined) hp.siteTitle = req.body.siteTitle;
  if (req.body.badge !== undefined) hp.hero.badge = req.body.badge;
  if (req.body.description !== undefined) hp.hero.description = req.body.description;
  if (req.body.stats !== undefined) hp.stats = req.body.stats;
  if (req.body.hero_karte !== undefined) hp.hero_karte = req.body.hero_karte;
  if (req.body.pruefung_karte !== undefined) hp.pruefung_karte = req.body.pruefung_karte;
  if (req.body.dojo_karte !== undefined) hp.dojo_karte = req.body.dojo_karte;
  if (req.body.cta !== undefined) hp.cta = req.body.cta;
  writeHomepage(hp);
  res.json({ ok: true });
  rebuildAndDeploy();
});

app.post('/api/homepage/image', upload.single('image'), async (req, res) => {
  try {
    const filename = 'hero.webp';
    await sharp(req.file.buffer)
      .resize(1200, 1200, { fit: 'inside', withoutEnlargement: true })
      .webp({ quality: 88 })
      .toFile(path.join(HERO_DIR, filename));
    const hp = readHomepage();
    hp.hero.image = filename;
    writeHomepage(hp);
    res.json({ ok: true, image: filename });
    rebuildAndDeploy();
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

app.use('/hero', express.static(HERO_DIR));
app.use('/uebermich-img', express.static(UEBERMICH_IMG_DIR));
app.use('/erfolge-img', express.static(ERFOLGE_IMG_DIR));
app.use('/gaestebuch-img', express.static(GAESTEBUCH_IMG_DIR));

// Über mich API
function readUebermich() {
  return JSON.parse(fs.readFileSync(UEBERMICH_FILE, 'utf8'));
}
function writeUebermich(data) {
  fs.writeFileSync(UEBERMICH_FILE, JSON.stringify(data, null, 2));
}

app.get('/api/uebermich', (req, res) => {
  res.json(readUebermich());
});

app.put('/api/uebermich', (req, res) => {
  const data = req.body;
  writeUebermich(data);
  res.json({ ok: true });
  rebuildAndDeploy();
});

app.post('/api/uebermich/image', upload.single('image'), async (req, res) => {
  try {
    const filename = 'portrait.webp';
    await sharp(req.file.buffer)
      .resize(800, 1000, { fit: 'cover', position: 'top' })
      .webp({ quality: 88 })
      .toFile(path.join(UEBERMICH_IMG_DIR, filename));
    const data = readUebermich();
    data.hero.image = filename;
    writeUebermich(data);
    res.json({ ok: true, image: filename });
    rebuildAndDeploy();
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// ── Erfolge API ───────────────────────────────────────────────
function readErfolge() {
  return JSON.parse(fs.readFileSync(ERFOLGE_FILE, 'utf8'));
}
function writeErfolge(data) {
  fs.writeFileSync(ERFOLGE_FILE, JSON.stringify(data, null, 2));
}

app.get('/api/erfolge', (req, res) => {
  res.json(readErfolge());
});

app.put('/api/erfolge', (req, res) => {
  writeErfolge(req.body);
  res.json({ ok: true });
  rebuildAndDeploy();
});

app.post('/api/erfolge/image', upload.single('image'), async (req, res) => {
  try {
    const filename = 'hero.webp';
    await sharp(req.file.buffer)
      .resize(1200, 1500, { fit: 'inside', withoutEnlargement: true })
      .webp({ quality: 88 })
      .toFile(path.join(ERFOLGE_IMG_DIR, filename));
    const data = readErfolge();
    data.hero.image = filename;
    writeErfolge(data);
    res.json({ ok: true, image: filename });
    rebuildAndDeploy();
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// ── Einzelerfolge (Markdown) API ──────────────────────────────
const ERFOLGE_CONTENT_DIR = path.join(__dirname, 'content/erfolge');

function parseFM(content) {
  const match = content.match(/^---\r?\n([\s\S]+?)\r?\n---\r?\n([\s\S]*)$/);
  if (!match) return { data: {}, content };
  const fm = match[1];
  const body = match[2];
  const data = {};
  fm.split('\n').forEach(line => {
    const [key, ...rest] = line.split(':');
    if (key && rest.length) data[key.trim()] = rest.join(':').trim().replace(/^"|"$/g, '');
  });
  return { data, content: body };
}

app.get('/api/individual-successes', (req, res) => {
  const files = fs.readdirSync(ERFOLGE_CONTENT_DIR).filter(f => f.endsWith('.md') && f !== '_index.md');
  const list = files.map(f => {
    const c = fs.readFileSync(path.join(ERFOLGE_CONTENT_DIR, f), 'utf8');
    const { data } = parseFM(c);
    return { fileName: f, title: data.title || f, rang: data.rang, image: data.image, weight: parseInt(data.weight) || 999 };
  });
  list.sort((a, b) => a.weight - b.weight);
  res.json(list);
});

app.put('/api/individual-successes/reorder', (req, res) => {
  const { order } = req.body;
  if (!Array.isArray(order)) return res.status(400).json({ ok: false });
  
  order.forEach((fileName, index) => {
    const filePath = path.join(ERFOLGE_CONTENT_DIR, fileName);
    if (!fs.existsSync(filePath)) return;
    
    const content = fs.readFileSync(filePath, 'utf8');
    const { data, content: body } = parseFM(content);
    
    data.weight = index + 1;
    
    let fmStr = '---\n';
    for (const k in data) {
      if (data[k] !== undefined && data[k] !== null) {
        if (k === 'weight') {
          fmStr += `${k}: ${data[k]}\n`;
        } else {
          fmStr += `${k}: "${data[k]}"\n`;
        }
      }
    }
    fmStr += '---\n';
    fs.writeFileSync(filePath, fmStr + '\n' + body);
  });
  
  res.json({ ok: true });
  rebuildAndDeploy();
});

app.get('/api/individual-success/:file', (req, res) => {
  const c = fs.readFileSync(path.join(ERFOLGE_CONTENT_DIR, req.params.file), 'utf8');
  const { data, content } = parseFM(c);
  res.json({ ...data, content });
});

app.put('/api/individual-success/:file', (req, res) => {
  const filePath = path.join(ERFOLGE_CONTENT_DIR, req.params.file);
  const oldContent = fs.readFileSync(filePath, 'utf8');
  const { data: oldData } = parseFM(oldContent);
  const { title, rang, summary, content, ort, datum, kategorie, is_weitere_auszeichnung, image, images } = req.body;
  
  const newData = { ...oldData, title, rang, summary, ort, datum, kategorie, is_weitere_auszeichnung };
  if (image !== undefined) newData.image = image;
  if (images !== undefined) newData.images = images;
  let fmStr = '---\n';
  for (const k in newData) {
    if (newData[k]) {
      if (k === 'weight') {
        fmStr += `${k}: ${newData[k]}\n`;
      } else {
        fmStr += `${k}: "${newData[k]}"\n`;
      }
    }
  }
  fmStr += '---\n';
  fs.writeFileSync(filePath, fmStr + '\n' + content);
  res.json({ ok: true });
  rebuildAndDeploy();
});

app.post('/api/individual-success/:file/images', upload.array('images', 5), async (req, res) => {
  try {
    const baseName = req.params.file.replace('.md', '');
    const filenames = [];
    
    for (const file of req.files) {
      const isVideo = file.mimetype.startsWith('video/');
      const origExt = path.extname(file.originalname).toLowerCase();
      const ext = isVideo ? origExt : '.webp';
      const filename = `success-${baseName}-${Date.now()}-${Math.random().toString(36).slice(2,7)}${ext}`;
      
      if (isVideo) {
        fs.writeFileSync(path.join(ERFOLGE_IMG_DIR, filename), file.buffer);
      } else {
        await sharp(file.buffer)
          .resize(1000, 1000, { fit: 'inside', withoutEnlargement: true })
          .webp({ quality: 85 })
          .toFile(path.join(ERFOLGE_IMG_DIR, filename));
      }
      filenames.push(filename);
    }
    
    // In Markdown Datei schreiben
    const filePath = path.join(ERFOLGE_CONTENT_DIR, req.params.file);
    const c = fs.readFileSync(filePath, 'utf8');
    const { data, content } = parseFM(c);
    
    let existingImages = [];
    try { existingImages = JSON.parse(req.body.existingImages || '[]'); } catch(e){}
    const allImages = [...existingImages, ...filenames];
    
    let mainIdx = parseInt(req.body.mainImageIndex) || 0;
    if (mainIdx < 0 || mainIdx >= allImages.length) mainIdx = 0;
    
    if (allImages.length > 0) {
      data.image = allImages[mainIdx]; // Vom User gewähltes Hauptbild
      data.images = allImages.join(',');
    } else {
      delete data.image;
      delete data.images;
    }
    
    let fmStr = '---\n';
    for (const k in data) {
      if (data[k]) fmStr += `${k}: "${data[k]}"\n`;
    }
    fmStr += '---\n';
    fs.writeFileSync(filePath, fmStr + '\n' + content);
    
    res.json({ ok: true, images: filenames });
    rebuildAndDeploy();
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// ── Galerie Seiten-Texte API ──────────────────────────────────
app.get('/api/galerie', (req, res) => {
  res.json(JSON.parse(fs.readFileSync(GALERIE_PAGE_FILE, 'utf8')));
});
app.put('/api/galerie', (req, res) => {
  fs.writeFileSync(GALERIE_PAGE_FILE, JSON.stringify(req.body, null, 2));
  res.json({ ok: true });
  rebuildAndDeploy();
});

// ── Gästebuch API ─────────────────────────────────────────────
function readGaestebuch() {
  return JSON.parse(fs.readFileSync(GAESTEBUCH_FILE, 'utf8'));
}
function writeGaestebuch(data) {
  fs.writeFileSync(GAESTEBUCH_FILE, JSON.stringify(data, null, 2));
}

app.get('/api/gaestebuch', (req, res) => {
  res.json(readGaestebuch());
});

app.put('/api/gaestebuch', (req, res) => {
  writeGaestebuch(req.body);
  res.json({ ok: true });
  rebuildAndDeploy();
});

// Öffentlicher Endpunkt für neue Einträge
app.post('/api/gaestebuch/public', (req, res) => {
  try {
    const { name, text, email, subject } = req.body;
    if (!name || !text) return res.status(400).json({ ok: false, error: 'Name und Text fehlen' });

    const data = readGaestebuch();
    const newEntry = {
      id: Date.now().toString(),
      name: name.trim(),
      rolle: subject || 'Besucher',
      text: text.trim(),
      farbe: 'default',
      breit: false,
      datum: new Date().toISOString()
    };

    data.eintraege.unshift(newEntry); // Oben anfügen
    writeGaestebuch(data);
    res.json({ ok: true });
    
    // Nach kurzem Delay bauen, damit der User nicht warten muss
    setTimeout(() => rebuildAndDeploy(), 500);
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

app.post('/api/gaestebuch/image', upload.single('image'), async (req, res) => {
  try {
    const filename = 'hero.webp';
    await sharp(req.file.buffer)
      .resize(1400, 600, { fit: 'cover', position: 'center' })
      .webp({ quality: 88 })
      .toFile(path.join(GAESTEBUCH_IMG_DIR, filename));
    const data = JSON.parse(fs.readFileSync(GAESTEBUCH_FILE, 'utf8'));
    data.hero.image = filename;
    fs.writeFileSync(GAESTEBUCH_FILE, JSON.stringify(data, null, 2));
    res.json({ ok: true, image: filename });
    rebuildAndDeploy();
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// ── Global (Social Links) API ─────────────────────────────────
app.get('/api/global', (req, res) => {
  res.json(JSON.parse(fs.readFileSync(GLOBAL_FILE, 'utf8')));
});
app.put('/api/global', (req, res) => {
  fs.writeFileSync(GLOBAL_FILE, JSON.stringify(req.body, null, 2));
  res.json({ ok: true });
  rebuildAndDeploy();
});

// ── Erfolge Interactions (Likes/Comments) API ─────────────────
function readErfolgeInteractions() {
  if (!fs.existsSync(ERFOLGE_INTERACTIONS_FILE)) {
    return {};
  }
  try {
    return JSON.parse(fs.readFileSync(ERFOLGE_INTERACTIONS_FILE, 'utf8'));
  } catch (e) {
    return {};
  }
}

function writeErfolgeInteractions(data) {
  fs.writeFileSync(ERFOLGE_INTERACTIONS_FILE, JSON.stringify(data, null, 2));
}

function getClientIp(req) {
  const forwarded = req.headers['x-forwarded-for'];
  if (forwarded) {
    return forwarded.split(',')[0].trim();
  }
  return req.ip || req.socket.remoteAddress;
}

app.get('/api/erfolge-interactions', (req, res) => {
  try {
    const clientIp = getClientIp(req);
    const data = readErfolgeInteractions();
    const sanitized = {};
    for (const id in data) {
      const item = data[id];
      const likedIps = item.likedIps || [];
      const comments = item.comments || [];
      
      // Omit IP from comments in public response (GDPR-compliant)
      const sanitizedComments = comments.map(c => ({
        id: c.id,
        name: c.name,
        text: c.text,
        date: c.date
      }));

      sanitized[id] = {
        likes: typeof item.likes === 'number' ? item.likes : likedIps.length,
        comments: sanitizedComments,
        likedByUser: likedIps.includes(clientIp),
        commentedByUser: comments.some(c => c.ip === clientIp)
      };
    }
    res.json(sanitized);
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

app.post('/api/erfolge-interactions/like', (req, res) => {
  try {
    const { id } = req.body;
    if (!id) return res.status(400).json({ ok: false, error: 'ID fehlt' });
    
    const clientIp = getClientIp(req);
    const interactions = readErfolgeInteractions();
    if (!interactions[id]) {
      interactions[id] = { likes: 0, likedIps: [], comments: [] };
    }
    if (!interactions[id].likedIps) {
      interactions[id].likedIps = [];
    }
    
    if (interactions[id].likedIps.includes(clientIp)) {
      // Already liked, just return current status (GDPR-compliant, no IP leak)
      return res.json({ 
        ok: true, 
        data: { 
          likes: interactions[id].likedIps.length, 
          comments: interactions[id].comments || [],
          likedByUser: true
        } 
      });
    }
    
    interactions[id].likedIps.push(clientIp);
    interactions[id].likes = interactions[id].likedIps.length;
    writeErfolgeInteractions(interactions);
    
    res.json({ 
      ok: true, 
      data: { 
        likes: interactions[id].likes, 
        comments: interactions[id].comments || [],
        likedByUser: true
      } 
    });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

app.post('/api/erfolge/interactions/unlike', (req, res) => {
  try {
    const { id } = req.body;
    if (!id) return res.status(400).json({ ok: false, error: 'ID fehlt' });
    
    const clientIp = getClientIp(req);
    const interactions = readErfolgeInteractions();
    if (interactions[id]) {
      if (!interactions[id].likedIps) {
        interactions[id].likedIps = [];
      }
      interactions[id].likedIps = interactions[id].likedIps.filter(ip => ip !== clientIp);
      interactions[id].likes = interactions[id].likedIps.length;
      writeErfolgeInteractions(interactions);
    }
    
    const current = interactions[id] || { likes: 0, comments: [] };
    res.json({ 
      ok: true, 
      data: { 
        likes: current.likes || 0, 
        comments: current.comments || [],
        likedByUser: false
      } 
    });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

app.post('/api/erfolge-interactions/comment', (req, res) => {
  try {
    const { id, name, text } = req.body;
    if (!id || !name || !text) return res.status(400).json({ ok: false, error: 'ID, Name oder Text fehlt' });
    
    const clientIp = getClientIp(req);
    const interactions = readErfolgeInteractions();
    if (!interactions[id]) {
      interactions[id] = { likes: 0, likedIps: [], comments: [] };
    }
    if (!interactions[id].comments) {
      interactions[id].comments = [];
    }
    
    // Check if client IP already commented on this success
    if (interactions[id].comments.some(c => c.ip === clientIp)) {
      return res.status(400).json({ ok: false, error: 'Du hast bereits einen Kommentar hinterlassen.' });
    }
    
    const newComment = {
      id: Date.now().toString() + '-' + Math.random().toString(36).slice(2, 7),
      name: name.trim(),
      text: text.trim(),
      date: new Date().toISOString(),
      ip: clientIp // Store IP for rate limiting
    };
    
    interactions[id].comments.push(newComment);
    writeErfolgeInteractions(interactions);
    
    // Omit IP from comments in public response
    const sanitizedComments = interactions[id].comments.map(c => ({
      id: c.id,
      name: c.name,
      text: c.text,
      date: c.date
    }));
    
    res.json({ 
      ok: true, 
      data: {
        likes: typeof interactions[id].likes === 'number' ? interactions[id].likes : (interactions[id].likedIps || []).length,
        comments: sanitizedComments,
        likedByUser: (interactions[id].likedIps || []).includes(clientIp),
        commentedByUser: true
      }, 
      comment: {
        id: newComment.id,
        name: newComment.name,
        text: newComment.text,
        date: newComment.date
      }
    });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// Admin-UI
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'admin.html'));
});

app.get('/__old', (req, res) => res.redirect('/'));


app.listen(PORT, '0.0.0.0', () => {
  console.log(`\n✨ MiyaKarate Admin läuft auf http://localhost:${PORT}\n`);
});
