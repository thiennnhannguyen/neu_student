import CareerIllustration, { ILLUSTRATIONS } from './CareerIllustration';
import '../../../styles/m12.css';

const NAMES = {
  frontend: 'Frontend',
  backend: 'Backend',
  fullstack: 'Full-stack',
  mobile: 'Mobile',
  ai: 'AI Engineer',
  data: 'Data Analyst',
  ba: 'Business Analyst',
  devops: 'DevOps',
  cybersecurity: 'Cybersecurity',
  qa: 'QA/Test',
};

/** Trang chỉ có ở dev, để duyệt cả 10 hình cùng lúc. */
export default function IllustrationsSheet() {
  return (
    <main className="illustrations-sheet">
      <h1>Minh họa 10 nghề</h1>
      <div className="illustrations-sheet__grid">
        {Object.keys(ILLUSTRATIONS).map((key) => (
          <figure key={key}>
            <CareerIllustration illustrationKey={key} />
            <figcaption>{NAMES[key]}</figcaption>
          </figure>
        ))}
      </div>
    </main>
  );
}
