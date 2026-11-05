import HealthStatus from './HealthStatus';

export default function HomePage() {
  return (
    <section className="card">
      <h1>Khung dự án M11, M12</h1>
      <p>Các chức năng sẽ được thêm theo từng giai đoạn. Toàn bộ dữ liệu là dữ liệu mẫu.</p>
      <h2>Trạng thái hệ thống</h2>
      <HealthStatus />
    </section>
  );
}
