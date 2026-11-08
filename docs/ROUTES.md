# Danh sách route

Sinh tự động từ `app.url_map` bằng `python -m scripts.list_routes`, không sửa tay.
Chính sách `public` là không cần đăng nhập. Còn lại là các vai trò được gọi; ngoài phạm vi dữ liệu
thì service trả 404. Route ghi (POST, PUT, PATCH, DELETE) còn cần header `X-Requested-With: fetch`.

Tổng 114 route, 7 route công khai.

## Route công khai

| Đường dẫn | Phương thức |
|---|---|
| `/` | GET |
| `/<spa:path>` | GET |
| `/api/auth/demo-accounts` | GET |
| `/api/auth/login` | POST |
| `/api/auth/me` | GET |
| `/api/health` | GET |
| `/api/public/certificates/<code>` | GET |

## Mọi route

| Đường dẫn | Phương thức | Chính sách |
|---|---|---|
| `/` | GET | public |
| `/<spa:path>` | GET | public |
| `/api/admin/audit-logs` | GET | admin |
| `/api/admin/audit-logs/entities` | GET | admin |
| `/api/admin/career-nodes/<node_id>` | DELETE | admin |
| `/api/admin/career-nodes/<node_id>` | GET | admin |
| `/api/admin/career-nodes/<node_id>` | PATCH | admin |
| `/api/admin/career-nodes/<node_id>/requirements` | POST | admin |
| `/api/admin/career-versions/<version_id>` | DELETE | admin |
| `/api/admin/career-versions/<version_id>` | GET | admin |
| `/api/admin/career-versions/<version_id>/nodes` | POST | admin |
| `/api/admin/career-versions/<version_id>/publish` | POST | admin |
| `/api/admin/careers` | GET | admin |
| `/api/admin/careers` | POST | admin |
| `/api/admin/careers/<career_id>` | DELETE | admin |
| `/api/admin/careers/<career_id>` | GET | admin |
| `/api/admin/careers/<career_id>` | PATCH | admin |
| `/api/admin/careers/<career_id>/versions` | GET | admin |
| `/api/admin/careers/<career_id>/versions` | POST | admin |
| `/api/admin/course-skill-mappings` | GET | admin |
| `/api/admin/course-skill-mappings` | POST | admin |
| `/api/admin/course-skill-mappings/<mapping_id>` | DELETE | admin |
| `/api/admin/course-skill-mappings/<mapping_id>` | GET | admin |
| `/api/admin/course-skill-mappings/<mapping_id>` | PATCH | admin |
| `/api/admin/course-skill-mappings/<mapping_id>/approve` | POST | admin |
| `/api/admin/grade-attempts` | POST | admin |
| `/api/admin/requirements/<requirement_id>` | DELETE | admin |
| `/api/admin/requirements/<requirement_id>` | GET | admin |
| `/api/admin/requirements/<requirement_id>` | PATCH | admin |
| `/api/admin/requirements/<requirement_id>/approve` | POST | admin |
| `/api/admin/skills` | GET | admin |
| `/api/admin/skills` | POST | admin |
| `/api/admin/skills/<skill_id>` | DELETE | admin |
| `/api/admin/skills/<skill_id>` | GET | admin |
| `/api/admin/skills/<skill_id>` | PATCH | admin |
| `/api/admin/students` | GET | admin |
| `/api/advisor/students` | GET | advisor |
| `/api/auth/demo-accounts` | GET | public |
| `/api/auth/login` | POST | public |
| `/api/auth/logout` | POST | admin, advisor, student, support_staff |
| `/api/auth/me` | GET | public |
| `/api/health` | GET | public |
| `/api/lms/calendar` | GET | admin, advisor |
| `/api/lms/form-options` | GET | admin, advisor |
| `/api/lms/preview` | POST | admin, advisor |
| `/api/lms/snapshots/latest` | GET | admin, advisor |
| `/api/lms/sync` | POST | admin, advisor |
| `/api/m11/compare` | GET | admin, advisor, student |
| `/api/m11/credits` | GET | admin, advisor, student |
| `/api/m11/current-courses` | GET | admin, advisor, student |
| `/api/m11/curriculum-check` | GET | admin, advisor, student |
| `/api/m11/gpa-trend` | GET | admin, advisor, student |
| `/api/m11/grades` | GET | admin, advisor, student |
| `/api/m11/grades/<course_id>/attempts` | GET | admin, advisor, student |
| `/api/m11/metrics-glossary` | GET | admin, advisor, student |
| `/api/m11/overview` | GET | admin, advisor, student |
| `/api/m11/risks` | GET | admin, advisor, student |
| `/api/m11/semesters` | GET | admin, advisor, student |
| `/api/m11/strengths` | GET | admin, advisor, student |
| `/api/m12/attempts/<attempt_id>` | GET | student |
| `/api/m12/attempts/<attempt_id>/answers/<question_id>` | PUT | student |
| `/api/m12/attempts/<attempt_id>/submit` | POST | student |
| `/api/m12/career-goal` | GET | admin, advisor, student |
| `/api/m12/career-goal` | PUT | student |
| `/api/m12/career-goal/history` | GET | admin, advisor, student |
| `/api/m12/careers` | GET | admin, advisor, student |
| `/api/m12/careers/<career_id>` | GET | admin, advisor, student |
| `/api/m12/careers/<career_id>/tree` | GET | admin, advisor, student |
| `/api/m12/careers/slug/<slug>` | GET | admin, advisor, student |
| `/api/m12/careers/slug/<slug>/framework` | GET | admin, advisor, student |
| `/api/m12/certificates` | GET | admin, advisor, student |
| `/api/m12/certificates/<code>` | GET | admin, advisor, student |
| `/api/m12/evidence-reviews` | GET | admin, advisor |
| `/api/m12/evidence-reviews/<evidence_id>` | GET | admin, advisor |
| `/api/m12/evidence-reviews/<evidence_id>/approve` | POST | advisor |
| `/api/m12/evidence-reviews/<evidence_id>/reject` | POST | advisor |
| `/api/m12/evidences` | GET | admin, advisor, student |
| `/api/m12/evidences` | POST | student |
| `/api/m12/evidences/<evidence_id>/attachments/<attachment_id>` | GET | admin, advisor, student, support_staff |
| `/api/m12/gallery` | GET | admin, advisor, student |
| `/api/m12/improvement-plan` | GET | admin, advisor, student |
| `/api/m12/improvement-plan` | POST | student |
| `/api/m12/improvement-plan/<plan_id>/items` | POST | student |
| `/api/m12/improvement-plan/<plan_id>/items/<item_id>` | DELETE | student |
| `/api/m12/improvement-plan/<plan_id>/items/<item_id>` | PATCH | student |
| `/api/m12/improvement-plan/<plan_id>/new-risks` | POST | student |
| `/api/m12/modules/<module_id>/attempts` | POST | student |
| `/api/m12/modules/<module_id>/review` | GET | student |
| `/api/m12/my-careers` | GET | admin, advisor, student |
| `/api/m12/progress/careers/<career_id>` | GET | admin, advisor, student |
| `/api/m12/progress/careers/slug/<slug>` | GET | admin, advisor, student |
| `/api/m12/related` | GET | admin, advisor, student |
| `/api/m12/requirements/<requirement_id>` | GET | admin, advisor, student |
| `/api/m12/roadmaps/<roadmap_id>/items/<item_id>` | PATCH | student |
| `/api/m12/roadmaps/<roadmap_id>/proposal` | GET | admin, advisor, student |
| `/api/m12/roadmaps/<roadmap_id>/proposal/accept` | POST | student |
| `/api/m12/roadmaps/<roadmap_id>/proposal/dismiss` | POST | student |
| `/api/m12/roadmaps/<roadmap_id>/versions` | GET | admin, advisor, student |
| `/api/m12/roadmaps/current` | GET | admin, advisor, student |
| `/api/m12/roadmaps/generate` | POST | student |
| `/api/m12/support-categories` | GET | admin, advisor, student, support_staff |
| `/api/m12/support-requests` | GET | admin, advisor, student, support_staff |
| `/api/m12/support-requests` | POST | student |
| `/api/m12/support-requests/<request_id>` | GET | admin, advisor, student, support_staff |
| `/api/m12/support-requests/<request_id>/attachments/<attachment_id>` | GET | admin, advisor, student, support_staff |
| `/api/m12/support-requests/<request_id>/messages` | POST | admin, advisor, student, support_staff |
| `/api/m12/support-requests/<request_id>/status` | POST | admin, advisor, student, support_staff |
| `/api/notifications` | GET | admin, advisor, student, support_staff |
| `/api/notifications/<int:notification_id>/read` | POST | admin, advisor, student, support_staff |
| `/api/notifications/read-all` | POST | admin, advisor, student, support_staff |
| `/api/public/certificates/<code>` | GET | public |
| `/api/students/<student_id>` | GET | admin, advisor, student |
| `/api/students/me` | GET | student |
| `/api/students/me/contact` | PATCH | student |
