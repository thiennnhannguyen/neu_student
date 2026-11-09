/**
 * D-324: link học W3Schools cho ô "Tự học ngoài chương trình". Khóa là đúng chuỗi trong cẩm nang
 * (careers.self_study). Chỉ gắn trang đã mở được ngày 2026-11-09; mục W3Schools không có bài
 * (Docker, Redis, OAuth/JWT, pytest/JUnit, CI/CD, Flutter/Dart, Power BI, Figma, Jira…) để chữ thường.
 */
const W3 = 'https://www.w3schools.com/';

const PAGES = {
  html: 'html/',
  css: 'css/',
  responsive: 'css/css_rwd_intro.asp',
  js: 'js/',
  typescript: 'typescript/',
  react: 'react/',
  express: 'nodejs/nodejs_express.asp',
  django: 'django/',
  http: 'tags/ref_httpmethods.asp',
  postgresql: 'postgresql/',
  sql: 'sql/',
  git: 'git/',
  python: 'python/',
  numpy: 'python/numpy/',
  pandas: 'python/pandas/',
  matplotlib: 'python/matplotlib_intro.asp',
  ml: 'python/python_ml_getting_started.asp',
  genai: 'gen_ai/',
  excel: 'excel/',
  statistics: 'statistics/',
  accessibility: 'accessibility/',
  bash: 'bash/',
  aws: 'aws/',
  webSecurity: 'cybersecurity/cybersecurity_web_applications.php',
};

const BY_ITEM = {
  HTML5: 'html',
  CSS3: 'css',
  responsive: 'responsive',
  'JavaScript ES6+': 'js',
  TypeScript: 'typescript',
  React: 'react',
  'React + TypeScript': 'react',
  'Node.js/Express hoặc Python FastAPI/Flask': 'express',
  'Flask/FastAPI/Django hoặc Spring Boot': 'django',
  'HTTP/REST': 'http',
  'REST API': 'http',
  REST: 'http',
  PostgreSQL: 'postgresql',
  SQL: 'sql',
  'SQL cơ bản': 'sql',
  'SQL window functions': 'sql',
  SQLite: 'sql',
  Git: 'git',
  'Git/GitHub Actions': 'git',
  Python: 'python',
  NumPy: 'numpy',
  Pandas: 'pandas',
  'Python Pandas': 'pandas',
  Matplotlib: 'matplotlib',
  'trực quan hóa': 'matplotlib',
  'scikit-learn': 'ml',
  'mô hình Transformer/LLM': 'genai',
  Excel: 'excel',
  'Excel nâng cao': 'excel',
  'A/B testing cơ bản': 'statistics',
  accessibility: 'accessibility',
  'Linux CLI/Bash': 'bash',
  Linux: 'bash',
  'AWS/Azure/GCP': 'aws',
  'OWASP API Security': 'webSecurity',
  'OWASP Top 10 & WSTG': 'webSecurity',
};

export function studyLink(item) {
  const page = PAGES[BY_ITEM[item]];
  return page ? W3 + page : null;
}
