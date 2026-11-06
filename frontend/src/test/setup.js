import '@testing-library/jest-dom/vitest';
import { cleanup, configure } from '@testing-library/react';
import { afterEach } from 'vitest';

// Mặc định findBy chờ 1 giây. Khi máy bận, test đầu của mỗi file còn phải biên dịch trang tải lazy
// nên vượt 1 giây dù hành vi đúng. Chỉ nới thời gian chờ tối đa, không làm test chạy lâu hơn khi đạt.
configure({ asyncUtilTimeout: 5000 });

afterEach(cleanup);
