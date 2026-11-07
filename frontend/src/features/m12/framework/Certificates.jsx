import qrcode from 'qrcode-generator';
import { Award, Printer } from 'lucide-react';
import { useMemo } from 'react';
import { useParams } from 'react-router';
import { Button, Card, EmptyState, PageHeader } from '../../../components/ui';
import { formatDateTime, withQuery } from '../../m11/format';
import { ResourceView } from '../../m11/ui';
import useApiResource from '../../m11/useApiResource';
import useCareerStudent from '../useCareerStudent';

export function verifyUrl(code) {
  return `${window.location.origin}/xac-thuc/${code}`;
}

/** Vẽ mã QR bằng SVG của React, không chèn HTML thô. */
export function QrCode({ value, label }) {
  const { size, cells } = useMemo(() => {
    const code = qrcode(0, 'M');
    code.addData(value);
    code.make();
    const count = code.getModuleCount();
    const dark = [];
    for (let row = 0; row < count; row += 1) {
      for (let column = 0; column < count; column += 1) {
        if (code.isDark(row, column)) {
          dark.push(`M${column} ${row}h1v1h-1z`);
        }
      }
    }
    return { size: count, cells: dark.join('') };
  }, [value]);
  return (
    <svg
      className="certificate__qr"
      role="img"
      aria-label={label}
      viewBox={`-2 -2 ${size + 4} ${size + 4}`}
      shapeRendering="crispEdges"
    >
      <rect x="-2" y="-2" width={size + 4} height={size + 4} className="certificate__qr-light" />
      <path d={cells} className="certificate__qr-dark" />
    </svg>
  );
}

function Certificate({ data }) {
  const url = verifyUrl(data.code);
  return (
    <article className="certificate">
      <p className="certificate__eyebrow">Chứng nhận hoàn thành bài kiểm tra</p>
      <h2 className="certificate__name">{data.student_name}</h2>
      <p>đã đạt bài kiểm tra mô-đun</p>
      <p className="certificate__module">{data.module_title}</p>
      <dl className="certificate__facts">
        <div>
          <dt>Điểm</dt>
          <dd>
            {data.correct_count}/{data.total} ({data.percent}%)
          </dd>
        </div>
        <div>
          <dt>Ngày cấp</dt>
          <dd>{formatDateTime(data.issued_at)}</dd>
        </div>
        <div>
          <dt>Mã chứng chỉ</dt>
          <dd className="certificate__code">{data.code}</dd>
        </div>
      </dl>
      <QrCode value={url} label="Mã QR tới trang xác thực" />
      <p className="certificate__url">{url}</p>
      <p className="certificate__notice">{data.notice}</p>
    </article>
  );
}

export function CertificatePage() {
  const { code } = useParams();
  const resource = useApiResource(`/api/m12/certificates/${code}`);
  return (
    <section className="certificate-page">
      <PageHeader
        title="Chứng chỉ"
        actions={
          <Button iconLeft={Printer} onClick={() => window.print()}>
            In hoặc lưu PDF
          </Button>
        }
      />
      <ResourceView
        resource={resource}
        loadingText="Đang tải chứng chỉ..."
        errorText="Không tải được chứng chỉ"
      >
        {(data) => <Certificate data={data} />}
      </ResourceView>
    </section>
  );
}

export function CertificatesPage() {
  const student = useCareerStudent();
  const resource = useApiResource(
    student.needsStudent ? null : withQuery('/api/m12/certificates', student.query),
  );
  return (
    <section className="certificate-page">
      <PageHeader title="Chứng chỉ của tôi" />
      {student.needsStudent ? (
        <EmptyState title="Chưa chọn sinh viên" />
      ) : (
        <ResourceView
          resource={resource}
          loadingText="Đang tải chứng chỉ..."
          errorText="Không tải được chứng chỉ"
          isEmpty={(data) => data.items.length === 0}
          emptyText="Chưa có chứng chỉ nào. Đạt bài kiểm tra mô-đun để nhận chứng chỉ."
        >
          {(data) => (
            <>
              <p className="framework__source">{data.notice}</p>
              <div className="framework-modules">
                {data.items.map((item) => (
                  <Card as="article" key={item.code}>
                    <h2 className="quiz-question__title">{item.module_title}</h2>
                    <p>
                      {item.correct_count}/{item.total} câu đúng · Cấp ngày{' '}
                      {formatDateTime(item.issued_at)}
                    </p>
                    <Button
                      variant="secondary"
                      iconLeft={Award}
                      to={student.link(`/m12/chung-chi/${item.code}`)}
                    >
                      Xem chứng chỉ
                    </Button>
                  </Card>
                ))}
              </div>
            </>
          )}
        </ResourceView>
      )}
    </section>
  );
}
