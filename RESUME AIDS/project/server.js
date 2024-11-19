import express from 'express';
import multer from 'multer';
import path from 'path';
import { fileURLToPath } from 'url';
import pdf from 'pdf-parse';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const upload = multer({ storage: multer.memoryStorage() });

app.use(express.static('public'));

function extractName(text) {
  const namePatterns = [
    /name:?\s*([A-Za-z\s]{2,50})/i,
    /^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})/,
    /(?:^|\n)([A-Za-z\s]{2,50})\s*(?:[\n]|$)/i
  ];

  for (const pattern of namePatterns) {
    const match = text.match(pattern);
    if (match && match[1]) {
      const name = match[1].trim();
      if (name.split(/\s+/).length >= 2 && name.length <= 50) {
        return name;
      }
    }
  }
  return null;
}

function extractEmail(text) {
  const emailPattern = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/;
  const match = text.match(emailPattern);
  return match ? match[0] : null;
}

function extractPhone(text) {
  const phonePatterns = [
    /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/,
    /\b\+\d{1,3}[-\s]?\d{1,4}[-\s]?\d{1,4}[-\s]?\d{1,4}\b/,
    /\(\d{3}\)\s*\d{3}[-.]?\d{4}/
  ];

  for (const pattern of phonePatterns) {
    const match = text.match(pattern);
    if (match) return match[0];
  }
  return null;
}

function extractSkills(text) {
  const technicalSkills = [
    'javascript', 'typescript', 'python', 'java', 'html', 'css', 'react', 
    'angular', 'vue', 'node', 'express', 'django', 'flask', 'sql', 'mysql', 
    'postgresql', 'mongodb', 'aws', 'azure', 'gcp', 'docker', 'kubernetes'
  ];

  const softSkills = [
    'leadership', 'communication', 'teamwork', 'problem solving',
    'project management', 'time management', 'analytical', 'creative'
  ];

  const found = {
    technical: [],
    soft: []
  };

  const textLower = text.toLowerCase();

  technicalSkills.forEach(skill => {
    if (textLower.includes(skill.toLowerCase())) {
      found.technical.push(skill);
    }
  });

  softSkills.forEach(skill => {
    if (textLower.includes(skill.toLowerCase())) {
      found.soft.push(skill);
    }
  });

  return found;
}

function extractExperience(text) {
  const experiences = [];
  const datePattern = /(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s.-]+\d{4}/gi;
  
  const sections = text.split(/\n\n+/);
  
  for (const section of sections) {
    const dates = section.match(datePattern) || [];
    if (dates.length >= 1) {
      const cleanText = section.replace(/\s+/g, ' ').trim();
      if (cleanText.length > 30) {
        experiences.push({
          dates,
          description: cleanText.slice(0, 500)
        });
      }
    }
  }

  return experiences.slice(0, 5);
}

function extractAchievements(text) {
  const achievements = new Set();
  const patterns = [
    /(achievement|accomplishment|award|honor|recognition)s?[:\s]+(.*?)(?:\n|$)/i,
    /(?:^|\n)[\s•-]*(won|achieved|earned|received|awarded)+(.*?)(?:\n|$)/i,
    /(?:^|\n)[\s•-]*(led|managed|developed|created|implemented)+(.*?)(?:\n|$)/i
  ];

  patterns.forEach(pattern => {
    const matches = text.matchAll(pattern);
    for (const match of matches) {
      const achievement = match[2].trim();
      if (achievement.length > 10) {
        achievements.add(achievement);
      }
    }
  });

  return [...achievements].slice(0, 5);
}

async function parseResume(buffer) {
  try {
    const data = await pdf(buffer);
    const text = data.text;

    return {
      name: extractName(text),
      email: extractEmail(text),
      phone: extractPhone(text),
      skills: extractSkills(text),
      experience: extractExperience(text),
      achievements: extractAchievements(text),
      raw_text: text.slice(0, 500) + (text.length > 500 ? '...' : '')
    };
  } catch (error) {
    console.error('Error parsing PDF:', error);
    throw new Error('Failed to parse PDF');
  }
}

app.post('/parse', upload.single('file'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }

  const fileType = req.file.originalname.toLowerCase();
  if (!fileType.endsWith('.pdf')) {
    return res.status(400).json({ error: 'Only PDF files are supported' });
  }

  try {
    const result = await parseResume(req.file.buffer);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});