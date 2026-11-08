import CurrentCourses from './CurrentCourses';
import M11Page from './M11Page';
import { RisksContent } from './RisksSection';

/**
 * Trang Phân tích & Cảnh báo (D-310): tập trung vào kỳ hiện tại.
 * Bỏ khỏi giao diện Xu hướng GPA, Tiến độ tín chỉ, Đối chiếu CTĐT, Điểm mạnh/yếu, So sánh hai kỳ;
 * các API vẫn còn. Dự đoán điểm và cảnh báo từng môn làm ở CR-13.
 */
export default function AnalysisPage() {
  return (
    <M11Page title="Phân tích & Cảnh báo" description="Cảnh báo học vụ và các môn đang học kỳ này.">
      {(scope) => (
        <div className="stack">
          <section aria-labelledby="academic-warning-title">
            <h2 id="academic-warning-title" className="section-heading">
              Cảnh báo học vụ
            </h2>
            <RisksContent scope={scope} />
          </section>
          <CurrentCourses scope={scope} />
        </div>
      )}
    </M11Page>
  );
}
