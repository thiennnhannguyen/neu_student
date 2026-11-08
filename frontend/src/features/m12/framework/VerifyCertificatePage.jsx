import { useParams } from 'react-router';
import MockNotice from '../../../components/MockNotice';
import { ResourceView } from '../../m11/ui';
import useApiResource from '../../m11/useApiResource';
import { formatDateTime } from '../../m11/format';

/** Trang công khai: chỉ tên, mô-đun, ngày cấp, hiệu lực. Không dùng logo của trường. */
export default function VerifyCertificatePage() {
  const { code } = useParams();
  const resource = useApiResource(`/api/public/certificates/${code}`);
  return (
    <main id="main" className="verify-page">
      <h1>Xác thực chứng chỉ</h1>
      <ResourceView
        resource={resource}
        loadingText="Đang kiểm tra mã chứng chỉ..."
        errorText="Không tìm thấy chứng chỉ với mã này"
      >
        {(data) => (
          <>
            <dl className="certificate__facts verify-page__facts">
              <div>
                <dt>Họ tên</dt>
                <dd>{data.student_name}</dd>
              </div>
              <div>
                <dt>Mô-đun</dt>
                <dd>{data.module_title}</dd>
              </div>
              <div>
                <dt>Ngày cấp</dt>
                <dd>{formatDateTime(data.issued_at)}</dd>
              </div>
              <div>
                <dt>Hiệu lực</dt>
                <dd>{data.valid ? 'Còn hiệu lực' : 'Đã thu hồi'}</dd>
              </div>
            </dl>
            <p className="certificate__notice">{data.notice}</p>
          </>
        )}
      </ResourceView>
      <MockNotice />
    </main>
  );
}
